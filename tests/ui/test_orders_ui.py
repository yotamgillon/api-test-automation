"""UI tests. Only data-testid selectors, no sleeps, auto-waiting expect assertions."""

import re

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.ui

ANY_ROW = re.compile(r"^order-row-")


def fill_form(page, customer="", item="", quantity=""):
    page.get_by_test_id("customer-input").fill(customer)
    page.get_by_test_id("item-input").fill(item)
    page.get_by_test_id("quantity-input").fill(str(quantity))


def submit(page, **fields):
    fill_form(page, **fields)
    page.get_by_test_id("submit-button").click()


def expect_row(page, order_id, customer, item, quantity, status="new"):
    row = page.get_by_test_id(f"order-row-{order_id}")
    expect(row).to_be_visible()
    expect(row.get_by_test_id("cell-customer")).to_have_text(customer)
    expect(row.get_by_test_id("cell-item")).to_have_text(item)
    expect(row.get_by_test_id("cell-quantity")).to_have_text(str(quantity))
    expect(row.get_by_test_id("cell-status")).to_have_text(status)


def test_empty_table_shows_empty_message(page):
    expect(page.get_by_test_id("empty-message")).to_be_visible()
    expect(page.get_by_test_id(ANY_ROW)).to_have_count(0)


def test_create_order_through_form_shows_it_in_table(page):
    submit(page, customer="Ann", item="Pen", quantity=2)

    expect_row(page, "ORD-0001", "Ann", "Pen", 2)
    expect(page.get_by_test_id("empty-message")).to_be_hidden()
    # the form is cleared after a successful submit
    expect(page.get_by_test_id("customer-input")).to_have_value("")
    expect(page.get_by_test_id("form-error")).to_have_text("")


def test_bug005_delete_removes_row_without_page_reload(page, make_order):
    """BUG-005: after a delete the table must update by itself, without a reload."""
    make_order(customer="First")
    make_order(customer="Second")
    page.reload()
    expect(page.get_by_test_id("order-row-ORD-0001")).to_be_visible()

    page.get_by_test_id("delete-ORD-0001").click()

    expect(page.get_by_test_id("order-row-ORD-0001")).to_have_count(0)


def test_create_two_orders_delete_one_keeps_the_other(page):
    submit(page, customer="Ann", item="Pen", quantity=1)
    expect_row(page, "ORD-0001", "Ann", "Pen", 1)
    submit(page, customer="Bob", item="Ink", quantity=5)
    expect_row(page, "ORD-0002", "Bob", "Ink", 5)

    page.get_by_test_id("delete-ORD-0001").click()

    expect(page.get_by_test_id("order-row-ORD-0001")).to_have_count(0)
    expect_row(page, "ORD-0002", "Bob", "Ink", 5)
    expect(page.get_by_test_id(ANY_ROW)).to_have_count(1)


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        pytest.param(
            {"customer": "", "item": "Pen", "quantity": 1}, "customer", id="missing-customer"
        ),
        pytest.param(
            {"customer": "Ann", "item": "Pen", "quantity": 0},
            "quantity must be between 1 and 100",
            id="quantity-0",
        ),
        pytest.param(
            {"customer": "Ann", "item": "Pen", "quantity": 101},
            "quantity must be between 1 and 100",
            id="quantity-101",
        ),
    ],
)
def test_invalid_form_shows_message_and_creates_no_order(page, client, fields, message):
    submit(page, **fields)

    expect(page.get_by_test_id("form-error")).to_contain_text(message)
    expect(page.get_by_test_id(ANY_ROW)).to_have_count(0)
    assert client.get("/orders").json() == []
