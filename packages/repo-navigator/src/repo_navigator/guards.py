"""Hard guards: allowlist, pinned revision, max bytes, secret-path block."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Paths that must never be read via tools (basename or path segment match).
SECRET_PATH_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(^|/)\.env(\.|$)"),
    re.compile(r"(^|/)\.env$"),
    re.compile(r"(^|/)credentials(\.|$)", re.I),
    re.compile(r"(^|/)secrets?(\.|$)", re.I),
    re.compile(r"(^|/)id_rsa"),
    re.compile(r"(^|/)\.pem$", re.I),
    re.compile(r"(^|/)aws[_-]?credentials", re.I),
    re.compile(r"(^|/)service[_-]?account.*\.json$", re.I),
    re.compile(r"(^|/)\.npmrc$"),
    re.compile(r"(^|/)\.netrc$"),
)

DEFAULT_MAX_READ_BYTES = 8192
DEFAULT_MAX_SYMBOL_LINES = 80


@dataclass
class RepoEntry:
    repo_id: str
    path: Path
    allowed_shas: set[str] | None = None  # None = any indexed SHA ok if pinned


@dataclass
class GuardConfig:
    repos: dict[str, RepoEntry] = field(default_factory=dict)
    max_read_bytes: int = DEFAULT_MAX_READ_BYTES
    max_symbol_lines: int = DEFAULT_MAX_SYMBOL_LINES
    maps_dir: Path = field(default_factory=lambda: Path("data/maps"))

    def require_repo(self, repo_id: str) -> RepoEntry:
        if not repo_id or repo_id not in self.repos:
            raise PermissionError(
                f"repo_id '{repo_id}' is not allowlisted. "
                f"Allowed: {sorted(self.repos)}"
            )
        return self.repos[repo_id]

    def require_pinned_sha(self, repo_id: str, git_sha: str) -> str:
        if not git_sha or not str(git_sha).strip():
            raise PermissionError("pinned git_sha is required (empty revision refused)")
        sha = str(git_sha).strip().lower()
        if not re.fullmatch(r"[0-9a-f]{7,40}", sha):
            raise PermissionError(f"git_sha must be a hex SHA (got {git_sha!r})")
        entry = self.require_repo(repo_id)
        if entry.allowed_shas is not None and sha not in entry.allowed_shas:
            # Also accept prefix match against allowlist
            if not any(a.startswith(sha) or sha.startswith(a) for a in entry.allowed_shas):
                raise PermissionError(
                    f"git_sha '{sha}' not in allowed revisions for '{repo_id}'"
                )
        return sha

    def assert_safe_relpath(self, relpath: str) -> str:
        if not relpath or relpath.startswith("/") or ".." in Path(relpath).parts:
            raise PermissionError(f"unsafe path refused: {relpath!r}")
        norm = relpath.replace("\\", "/")
        for pat in SECRET_PATH_PATTERNS:
            if pat.search(norm):
                raise PermissionError(f"secret path blocked: {relpath}")
        return norm

    def clamp_bytes(self, data: bytes | str) -> str:
        if isinstance(data, bytes):
            raw = data
            text = data.decode("utf-8", errors="replace")
        else:
            text = data
            raw = data.encode("utf-8")
        if len(raw) > self.max_read_bytes:
            # Truncate on byte boundary approximately
            truncated = raw[: self.max_read_bytes]
            text = truncated.decode("utf-8", errors="replace")
            return text + f"\n… [truncated at {self.max_read_bytes} bytes]"
        return text


def load_config(path: Path | None = None) -> GuardConfig:
    """Load allowlist config. Env REPO_NAVIGATOR_CONFIG overrides default path."""
    cfg_path = path
    if cfg_path is None:
        env = os.environ.get("REPO_NAVIGATOR_CONFIG")
        if env:
            cfg_path = Path(env)
        else:
            # Prefer package-adjacent config.yaml, then cwd
            here = Path(__file__).resolve().parents[2]
            candidates = [
                here / "config.yaml",
                Path.cwd() / "config.yaml",
            ]
            cfg_path = next((c for c in candidates if c.is_file()), candidates[0])

    if not cfg_path.is_file():
        raise FileNotFoundError(f"config not found: {cfg_path}")

    raw: dict[str, Any] = yaml.safe_load(cfg_path.read_text()) or {}
    root = cfg_path.parent.resolve()
    repos: dict[str, RepoEntry] = {}
    for rid, meta in (raw.get("repos") or {}).items():
        p = Path(meta["path"])
        if not p.is_absolute():
            p = (root / p).resolve()
        allowed = meta.get("allowed_shas")
        repos[rid] = RepoEntry(
            repo_id=rid,
            path=p,
            allowed_shas=set(s.lower() for s in allowed) if allowed else None,
        )

    maps = raw.get("maps_dir", "data/maps")
    maps_path = Path(maps)
    if not maps_path.is_absolute():
        maps_path = (root / maps_path).resolve()

    return GuardConfig(
        repos=repos,
        max_read_bytes=int(raw.get("max_read_bytes", DEFAULT_MAX_READ_BYTES)),
        max_symbol_lines=int(raw.get("max_symbol_lines", DEFAULT_MAX_SYMBOL_LINES)),
        maps_dir=maps_path,
    )


def is_secret_path(relpath: str) -> bool:
    norm = relpath.replace("\\", "/")
    return any(p.search(norm) for p in SECRET_PATH_PATTERNS)
