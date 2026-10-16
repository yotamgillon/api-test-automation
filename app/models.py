from typing import Annotated

from pydantic import BaseModel, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]

MIN_QUANTITY = 1
MAX_QUANTITY = 100

STATUSES = ("new", "paid", "shipped", "delivered", "cancelled")

# Allowed status transitions. Anything else is rejected with 409.
TRANSITIONS: dict[str, set[str]] = {
    "new": {"paid", "cancelled"},
    "paid": {"shipped", "cancelled"},
    "shipped": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}


class OrderCreate(BaseModel):
    id: Text | None = None
    customer: Text
    item: Text
    quantity: int


class OrderUpdate(BaseModel):
    customer: Text | None = None
    item: Text | None = None
    quantity: int | None = None
    status: str | None = None


class Order(BaseModel):
    id: str
    customer: str
    item: str
    quantity: int
    status: str
