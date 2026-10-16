# Test plan: Orders service

## 1. Scope
System under test: a small FastAPI "orders" service with in-memory storage and one HTML page (a form and a table). Everything runs locally, so results do not depend on external sites.

In scope: the REST API (`/orders`), input validation, status transitions, response shapes, and the browser page (create, list, delete, validation messages).

## 2. Requirements
| ID | Requirement |
|---|---|
| REQ-001 | `POST /orders` creates an order with status `new` and returns 201. The id is optional; if missing it is generated as ORD-0001, ORD-0002, ... |
| REQ-002 | `customer` and `item` are required, non-blank text; a missing or blank field returns 422. |
| REQ-003 | `quantity` is required and must be an integer from 1 to 100 inclusive; anything else returns 422. |
| REQ-004 | Order ids are unique; creating a duplicate id returns 409 and leaves the first order untouched. |
| REQ-005 | `GET /orders/{id}` returns the order, or 404 if it does not exist. |
| REQ-006 | `GET /orders` returns every order in creation order. |
| REQ-007 | `PUT /orders/{id}` is a partial update: only the fields sent change; a missing order returns 404. |
| REQ-008 | Status moves only along new -> paid or cancelled, paid -> shipped or cancelled, shipped -> delivered. Any other change to a different status returns 409. An unknown status value returns 422. |
| REQ-009 | `DELETE /orders/{id}` returns 204 and removes the order; a missing order returns 404. |
| REQ-010 | Responses have the documented shape: orders have exactly id, customer, item, quantity, status; errors have exactly `detail` (string). |
| REQ-011 | UI: submitting the form creates an order and shows it in the table with the right values. |
| REQ-012 | UI: deleting an order removes its row without a page reload and keeps the other rows. |
| REQ-013 | UI: invalid input shows the server's validation message and creates no order. |
| REQ-014 | `/_reset` (test support) exists only when `ENABLE_TEST_ENDPOINTS=1`. |

## 3. Decisions taken where the requirements were open
- `PUT` is a partial update. An empty body is a valid no-op (200).
- Sending the current status again (for example new -> new) is allowed and returns 200. It is idempotent, not an error.
- BUG-002 (status code of a missing order) and BUG-004 (invalid status transitions) are not visible in the UI, because the page never reads a single order and has no control to change a status. They are caught by API tests only.
- Order ids come from a counter that `/_reset` restarts, so tests are deterministic.

## 4. Test levels
| Level | Count | Tool | What it is for |
|---|---|---|---|
| API | 79 | pytest + httpx against a real uvicorn server in a background thread | Business rules, validation, boundaries, transitions, schemas. Fast and precise. |
| UI | 7 | Playwright (Python, Chromium headless) | Only what needs a browser: the form, the table, refresh after delete, validation messages. |

The counts come from `results/test_counts.txt` (`pytest --collect-only -q` for `tests/api` and `tests/ui`).

There is no separate unit level: the app is small and its logic is only reachable through HTTP routes, so API tests act as the lowest level. The bulk of the checks sit at the API level (about 92 percent of tests) because they are faster and fail with a clearer cause than browser tests.

## 5. Risks and how they are handled
| Risk | Handling |
|---|---|
| Wrong money or stock data from bad quantities | Boundary tests for 1 and 100, plus -1, 0, 101, a decimal and text. |
| Illegal order lifecycle | Full 5 x 5 transition matrix (20 pairs), expected values written from the spec, not from the app. |
| Missing data in listings | List test with exact count and exact ids for 1, 2 and 5 orders. |
| UI shows stale data | UI test deletes a row and asserts it disappears without a reload. |
| Flaky browser tests | No sleeps; Playwright auto-waiting `expect` with a 2000 ms timeout; the page sets `data-loaded` after its first fetch; fresh browser context and server reset per test. |
| Tests that only pass by accident | A deliberately buggy mode (`BUGGY_MODE`) shows each test failing on the right bug (see README). |

## 6. Not covered
- Performance and load.
- Security (authentication, injection, authorization). The service has none.
- Concurrency (parallel requests, race conditions).
- Persistence: storage is in memory and lost on restart.
- Accessibility.
- Cross-browser: only Chromium is used.
- Responsive layout and visual appearance.
- JavaScript coverage: coverage.py measures the Python code in `app/` only, not the script inside `index.html`.
- Long input values beyond the 50 character field limit, and non-ASCII text.

## 7. Traceability
Every test name below is checked against `pytest --collect-only` (parametrized tests are listed by function name).

| Requirement | Tests |
|---|---|
| REQ-001 | `test_create_order_returns_201_and_status_new`, `test_create_order_with_explicit_id_keeps_it`, `test_generated_ids_are_sequential_and_reset_restarts_the_counter`, `test_create_response_matches_order_schema` |
| REQ-002 | `test_missing_required_field_returns_422`, `test_blank_text_field_returns_422`, `test_invalid_json_types_return_422` |
| REQ-003 | `test_create_quantity_boundaries`, `test_update_quantity_boundaries`, `test_bug001_negative_quantity_is_rejected_and_not_stored` |
| REQ-004 | `test_duplicate_id_returns_409`, `test_generated_id_skips_an_id_already_taken_by_a_client_chosen_id` |
| REQ-005 | `test_get_existing_order_returns_it`, `test_bug002_get_missing_order_returns_404`, `test_delete_then_get_returns_404`, `test_get_response_matches_order_schema` |
| REQ-006 | `test_list_is_empty_when_no_orders`, `test_bug003_list_returns_every_created_order`, `test_list_response_items_match_order_schema` |
| REQ-007 | `test_update_changes_only_the_given_fields`, `test_update_with_empty_body_changes_nothing`, `test_update_missing_order_returns_404`, `test_update_response_matches_order_schema` |
| REQ-008 | `test_status_transition`, `test_bug004_new_order_cannot_jump_straight_to_delivered`, `test_same_status_update_is_an_accepted_noop`, `test_unknown_status_value_returns_422`, `test_conflict_response_matches_error_schema` |
| REQ-009 | `test_delete_returns_204_and_removes_only_that_order`, `test_delete_missing_order_returns_404`, `test_delete_twice_second_call_returns_404`, `test_delete_response_has_empty_body` |
| REQ-010 | `test_create_response_matches_order_schema`, `test_get_response_matches_order_schema`, `test_list_response_items_match_order_schema`, `test_update_response_matches_order_schema`, `test_error_responses_match_error_schema`, `test_conflict_response_matches_error_schema` |
| REQ-011 | `test_empty_table_shows_empty_message`, `test_create_order_through_form_shows_it_in_table`, `test_index_page_is_served` |
| REQ-012 | `test_bug005_delete_removes_row_without_page_reload`, `test_create_two_orders_delete_one_keeps_the_other` |
| REQ-013 | `test_invalid_form_shows_message_and_creates_no_order` |
| REQ-014 | `test_reset_endpoint_is_hidden_unless_test_endpoints_are_enabled` |

## 8. Entry and exit
- Entry: dependencies installed, Chromium installed (`make install`).
- Exit: `make test` is fully green on the correct app, and `make test-each-bug` shows at least one failing test for every seeded bug.
