"""In-memory order storage. Ids come from a counter, never from random or time."""

from app.models import Order


class Store:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.orders: dict[str, Order] = {}
        self._counter = 0

    def next_id(self) -> str:
        while True:
            self._counter += 1
            candidate = f"ORD-{self._counter:04d}"
            if candidate not in self.orders:
                return candidate


store = Store()
