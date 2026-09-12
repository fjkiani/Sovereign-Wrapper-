"""Helpers for the demo ledger."""


def normalize_name(name: str) -> str:
    return name.strip().lower()


def score_items(pairs: list[tuple[str, float]]) -> list[tuple[str, float]]:
    return sorted(pairs, key=lambda p: (-p[1], p[0]))
