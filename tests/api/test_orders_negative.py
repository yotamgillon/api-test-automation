"""Negative tests: invalid input and missing resources must be rejected clearly."""

import pytest

pytestmark = pytest.mark.api


def test_duplicate_id_returns_409(client, make_order):
    make_order(id="DUP-1")
    response = client.post(
        "/orders", json={"id": "DUP-1", "customer": "A", "item": "B", "quantity": 1}
    )
    assert response.status_code == 409
    assert client.get("/orders/DUP-1").json()["customer"] == "Alice"


@pytest.mark.parametrize("missing", ["customer", "item", "quantity"])
def test_missing_required_field_returns_422(client, missing):
    payload = {"customer": "Ann", "item": "Pen", "quantity": 1}
    del payload[missing]
    response = client.post("/orders", json=payload)
    assert response.status_code == 422
    assert missing in response.json()["detail"]


@pytest.mark.parametrize("field", ["customer", "item"])
@pytest.mark.parametrize("value", ["", "   "])
def test_blank_text_field_returns_422(client, field, value):
    payload = {"customer": "Ann", "item": "Pen", "quantity": 1, field: value}
    assert client.post("/orders", json=payload).status_code == 422


def test_bug001_negative_quantity_is_rejected_and_not_stored(client):
    """BUG-001: a negative quantity must return 422 and must not create an order."""
    response = client.post("/orders", json={"customer": "Ann", "item": "Pen", "quantity": -5})
    assert response.status_code == 422
    assert client.get("/orders").json() == []


def test_bug002_get_missing_order_returns_404(client):
    """BUG-002: asking for an order that does not exist must return 404."""
    response = client.get("/orders/DOES-NOT-EXIST")
    assert response.status_code == 404


def test_update_missing_order_returns_404(client):
    assert client.put("/orders/NOPE", json={"quantity": 2}).status_code == 404


def test_delete_missing_order_returns_404(client):
    assert client.delete("/orders/NOPE").status_code == 404


def test_delete_then_get_returns_404(client, make_order):
    order = make_order()
    assert client.delete(f"/orders/{order['id']}").status_code == 204
    assert client.get(f"/orders/{order['id']}").status_code == 404


def test_delete_twice_second_call_returns_404(client, make_order):
    order = make_order()
    assert client.delete(f"/orders/{order['id']}").status_code == 204
    assert client.delete(f"/orders/{order['id']}").status_code == 404


def test_unknown_status_value_returns_422(client, make_order):
    order = make_order()
    assert client.put(f"/orders/{order['id']}", json={"status": "teleported"}).status_code == 422


def test_invalid_json_types_return_422(client):
    payload = {"customer": 123, "item": ["x"], "quantity": 1}
    assert client.post("/orders", json=payload).status_code == 422


def test_reset_endpoint_is_hidden_unless_test_endpoints_are_enabled(client, monkeypatch):
    monkeypatch.setenv("ENABLE_TEST_ENDPOINTS", "0")
    assert client.post("/_reset").status_code == 404
