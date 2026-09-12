"""Tiny demo library for RepoNavigator fixture indexing."""

from demo_repo.utils import normalize_name, score_items


class Ledger:
    """In-memory client ledger."""

    def __init__(self) -> None:
        self._rows: dict[str, float] = {}

    def credit(self, client_id: str, amount: float) -> None:
        key = normalize_name(client_id)
        self._rows[key] = self._rows.get(key, 0.0) + amount

    def balance(self, client_id: str) -> float:
        return self._rows.get(normalize_name(client_id), 0.0)


def rank_clients(ledger: Ledger, client_ids: list[str]) -> list[tuple[str, float]]:
    """Return clients sorted by balance descending."""
    pairs = [(cid, ledger.balance(cid)) for cid in client_ids]
    return score_items(pairs)


def main() -> None:
    ledger = Ledger()
    ledger.credit("acme", 10.0)
    ledger.credit("beta", 3.5)
    print(rank_clients(ledger, ["acme", "beta"]))


if __name__ == "__main__":
    main()
