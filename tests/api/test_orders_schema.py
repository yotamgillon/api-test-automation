"""Response schema validation (strict types, no unexpected keys)."""

import pytest
from schemas import ErrorSchema, OrderSchema

pytestmark = pytest.mark.api


def test_create_response_matches_order_schema(client):
    response = client.post("/orders", json={"customer": "Ann", "item": "Pen", "quantity": 3})
    OrderSchema.model_validate(response.json())


def test_get_response_matches_order_schema(client, make_order):
    order = make_order()
    OrderSchema.model_validate(client.get(f"/orders/{order['id']}").json())


def test_list_response_items_match_order_schema(client, make_order):
    for i in range(3):
        make_order(customer=f"C{i}")
    body = client.get("/orders").json()
    assert isinstance(body, list)
    for item in body:
        OrderSchema.model_validate(item)


def test_update_response_matches_order_schema(client, make_order):
    order = make_order()
    response = client.put(f"/orders/{order['id']}", json={"status": "paid"})
    OrderSchema.model_validate(response.json())


def test_delete_response_has_empty_body(client, make_order):
    order = make_order()
    response = client.delete(f"/orders/{order['id']}")
    assert response.status_code == 204
    assert response.content == b""


@pytest.mark.parametrize(
    ("method", "path", "payload", "expected_status"),
    [
        pytest.param("get", "/orders/NOPE", None, 404, id="404-get"),
        pytest.param("post", "/orders", {"customer": "A"}, 422, id="422-missing-fields"),
        pytest.param(
            "post", "/orders", {"customer": "A", "item": "B", "quantity": 0}, 422, id="422-quantity"
        ),
    ],
)
def test_error_responses_match_error_schema(client, method, path, payload, expected_status):
    response = client.request(method, path, json=payload)
    assert response.status_code == expected_status
    ErrorSchema.model_validate(response.json())


def test_conflict_response_matches_error_schema(client, order_in_status):
    order_id = order_in_status("new")
    response = client.put(f"/orders/{order_id}", json={"status": "delivered"})
    assert response.status_code == 409
    ErrorSchema.model_validate(response.json())
