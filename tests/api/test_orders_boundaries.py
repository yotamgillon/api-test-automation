"""Boundary values for quantity. Spec: an integer from 1 to 100 inclusive."""

import pytest

pytestmark = pytest.mark.api

QUANTITY_CASES = [
    pytest.param(-1, 422, id="minus-one"),
    pytest.param(0, 422, id="zero"),
    pytest.param(1, 201, id="min-valid"),
    pytest.param(100, 201, id="max-valid"),
    pytest.param(101, 422, id="above-max"),
    pytest.param(1.5, 422, id="non-integer"),
    pytest.param("abc", 422, id="not-a-number"),
]


@pytest.mark.parametrize(("quantity", "expected_status"), QUANTITY_CASES)
def test_create_quantity_boundaries(client, quantity, expected_status):
    payload = {"customer": "Ann", "item": "Pen", "quantity": quantity}
    assert client.post("/orders", json=payload).status_code == expected_status


@pytest.mark.parametrize(("quantity", "create_status"), QUANTITY_CASES)
def test_update_quantity_boundaries(client, make_order, quantity, create_status):
    order = make_order()
    expected_status = 200 if create_status == 201 else 422
    response = client.put(f"/orders/{order['id']}", json={"quantity": quantity})
    assert response.status_code == expected_status
    if expected_status == 422:
        assert client.get(f"/orders/{order['id']}").json()["quantity"] == 1
