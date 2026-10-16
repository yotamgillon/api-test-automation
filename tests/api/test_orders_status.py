"""Status transitions. The expected table below is written from the spec, not from the app.

Allowed: new -> paid | cancelled, paid -> shipped | cancelled, shipped -> delivered.
Every other change to a different status is rejected with 409.
"""

import pytest

pytestmark = pytest.mark.api

STATUSES = ["new", "paid", "shipped", "delivered", "cancelled"]
ALLOWED = {
    ("new", "paid"),
    ("new", "cancelled"),
    ("paid", "shipped"),
    ("paid", "cancelled"),
    ("shipped", "delivered"),
}
TRANSITION_CASES = [
    pytest.param(src, dst, 200 if (src, dst) in ALLOWED else 409, id=f"{src}-to-{dst}")
    for src in STATUSES
    for dst in STATUSES
    if src != dst
]


@pytest.mark.parametrize(("source", "target", "expected_status"), TRANSITION_CASES)
def test_status_transition(client, order_in_status, source, target, expected_status):
    order_id = order_in_status(source)
    response = client.put(f"/orders/{order_id}", json={"status": target})
    assert response.status_code == expected_status
    stored = client.get(f"/orders/{order_id}").json()["status"]
    assert stored == (target if expected_status == 200 else source)


def test_bug004_new_order_cannot_jump_straight_to_delivered(client, make_order):
    """BUG-004: skipping paid and shipped must be rejected with 409 and leave status as new."""
    order = make_order()
    response = client.put(f"/orders/{order['id']}", json={"status": "delivered"})
    assert response.status_code == 409
    assert client.get(f"/orders/{order['id']}").json()["status"] == "new"


@pytest.mark.parametrize("status", STATUSES)
def test_same_status_update_is_an_accepted_noop(client, order_in_status, status):
    # Documented decision: re-sending the current status is idempotent (200), not an error.
    order_id = order_in_status(status)
    response = client.put(f"/orders/{order_id}", json={"status": status})
    assert response.status_code == 200
    assert response.json()["status"] == status
