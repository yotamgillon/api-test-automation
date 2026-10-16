"""Happy paths.

Spec used by all API tests:
- POST /orders creates an order (201) with status "new"; id is optional and, if absent,
  is generated as ORD-0001, ORD-0002, ... (counter, reset by /_reset).
- GET /orders lists every order in creation order; GET /orders/{id} returns one.
- PUT /orders/{id} partially updates fields and/or moves the status.
- DELETE /orders/{id} removes an order (204).
"""

import pytest

pytestmark = pytest.mark.api


def test_create_order_returns_201_and_status_new(client):
    response = client.post("/orders", json={"customer": "Ann", "item": "Pen", "quantity": 2})
    assert response.status_code == 201
    assert response.json() == {
        "id": "ORD-0001",
        "customer": "Ann",
        "item": "Pen",
        "quantity": 2,
        "status": "new",
    }


def test_create_order_with_explicit_id_keeps_it(make_order):
    assert make_order(id="CUSTOM-1")["id"] == "CUSTOM-1"


def test_generated_ids_are_sequential_and_reset_restarts_the_counter(client, make_order):
    assert [make_order()["id"] for _ in range(3)] == ["ORD-0001", "ORD-0002", "ORD-0003"]
    assert client.post("/_reset").status_code == 204
    assert make_order()["id"] == "ORD-0001"


def test_generated_id_skips_an_id_already_taken_by_a_client_chosen_id(client, make_order):
    # A client may pick the id the counter would hand out next. The generated id must differ.
    make_order(id="ORD-0001", customer="Chosen")

    response = client.post("/orders", json={"customer": "Generated", "item": "Pen", "quantity": 1})

    assert response.status_code == 201
    generated_id = response.json()["id"]
    assert generated_id != "ORD-0001"
    assert generated_id == "ORD-0002"
    assert client.get("/orders/ORD-0001").json()["customer"] == "Chosen"
    assert client.get(f"/orders/{generated_id}").json()["customer"] == "Generated"


def test_get_existing_order_returns_it(client, make_order):
    created = make_order(customer="Bob")
    response = client.get(f"/orders/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_list_is_empty_when_no_orders(client):
    response = client.get("/orders")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("count", [1, 2, 5])
def test_bug003_list_returns_every_created_order(client, make_order, count):
    """BUG-003: the list endpoint must return all N orders, including the last one."""
    created_ids = [make_order(customer=f"Customer {i}")["id"] for i in range(count)]
    listed = client.get("/orders").json()
    assert len(listed) == count
    assert [o["id"] for o in listed] == created_ids


def test_update_changes_only_the_given_fields(client, make_order):
    order = make_order(customer="Ann", item="Pen", quantity=2)
    response = client.put(f"/orders/{order['id']}", json={"quantity": 7})
    assert response.status_code == 200
    assert response.json() == {**order, "quantity": 7}
    assert client.get(f"/orders/{order['id']}").json()["quantity"] == 7


def test_update_with_empty_body_changes_nothing(client, make_order):
    # Documented decision: an empty partial update is a valid no-op.
    order = make_order()
    response = client.put(f"/orders/{order['id']}", json={})
    assert response.status_code == 200
    assert response.json() == order


def test_delete_returns_204_and_removes_only_that_order(client, make_order):
    keep = make_order(customer="Keep")
    drop = make_order(customer="Drop")
    assert client.delete(f"/orders/{drop['id']}").status_code == 204
    assert client.get(f"/orders/{keep['id']}").status_code == 200
    assert client.get(f"/orders/{drop['id']}").status_code == 404


def test_index_page_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert 'data-testid="orders-table"' in response.text
