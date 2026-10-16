"""Orders service: the system under test.

BUGGY_MODE switches on deliberately seeded bugs:
  BUGGY_MODE=1                  all bugs
  BUGGY_MODE=BUG-003            one bug
  BUGGY_MODE=BUG-001,BUG-005    a comma list
Unset, empty or any other value means the app behaves correctly. The variable is read
on every request (never at import time) so tests can flip it without reloading the app.
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response

from app.models import (
    MAX_QUANTITY,
    MIN_QUANTITY,
    STATUSES,
    TRANSITIONS,
    Order,
    OrderCreate,
    OrderUpdate,
)
from app.store import store

INDEX_HTML = Path(__file__).parent / "static" / "index.html"

app = FastAPI(title="Orders service")


def buggy(bug_id: str) -> bool:
    mode = os.getenv("BUGGY_MODE", "").strip()
    if mode == "1":
        return True
    return bug_id in {part.strip() for part in mode.split(",")}


def test_endpoints_enabled() -> bool:
    return os.getenv("ENABLE_TEST_ENDPOINTS") == "1"


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    parts = [f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "; ".join(parts)})


def check_quantity(quantity: int) -> None:
    # BUG-001 (BUGGY_MODE): the lower bound is not enforced.
    if buggy("BUG-001"):
        low_ok = True
    else:
        low_ok = quantity >= MIN_QUANTITY
    if not low_ok or quantity > MAX_QUANTITY:
        raise HTTPException(422, f"quantity must be between {MIN_QUANTITY} and {MAX_QUANTITY}")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    flag = "1" if buggy("BUG-005") else "0"
    return INDEX_HTML.read_text().replace("__BUGGY__", flag)


@app.post("/orders", status_code=201, response_model=Order)
def create_order(body: OrderCreate) -> Order:
    check_quantity(body.quantity)
    order_id = body.id or store.next_id()
    if order_id in store.orders:
        raise HTTPException(409, f"order {order_id} already exists")
    order = Order(
        id=order_id,
        customer=body.customer,
        item=body.item,
        quantity=body.quantity,
        status="new",
    )
    store.orders[order_id] = order
    return order


@app.get("/orders", response_model=list[Order])
def list_orders() -> list[Order]:
    orders = list(store.orders.values())
    # BUG-003 (BUGGY_MODE): the last item is dropped from the list.
    if buggy("BUG-003"):
        return orders[:-1]
    return orders


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = store.orders.get(order_id)
    if order is None:
        # BUG-002 (BUGGY_MODE): wrong status code for a missing order.
        if buggy("BUG-002"):
            return JSONResponse(status_code=200, content={"detail": "order not found"})
        raise HTTPException(404, "order not found")
    return order


@app.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: str, body: OrderUpdate) -> Order:
    order = store.orders.get(order_id)
    if order is None:
        raise HTTPException(404, "order not found")
    if body.quantity is not None:
        check_quantity(body.quantity)
    if body.status is not None:
        if body.status not in STATUSES:
            raise HTTPException(422, f"status must be one of {', '.join(STATUSES)}")
        # BUG-004 (BUGGY_MODE): any transition is accepted.
        allowed = body.status == order.status or body.status in TRANSITIONS[order.status]
        if not allowed and not buggy("BUG-004"):
            raise HTTPException(409, f"cannot change status from {order.status} to {body.status}")
    changes = body.model_dump(exclude_none=True)
    updated = order.model_copy(update=changes)
    store.orders[order_id] = updated
    return updated


@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: str) -> Response:
    if order_id not in store.orders:
        raise HTTPException(404, "order not found")
    del store.orders[order_id]
    return Response(status_code=204)


@app.post("/_reset", status_code=204)
def reset() -> Response:
    """Test-only: clears all orders and the id counter. Needs ENABLE_TEST_ENDPOINTS=1."""
    if not test_endpoints_enabled():
        raise HTTPException(404, "not found")
    store.reset()
    return Response(status_code=204)
