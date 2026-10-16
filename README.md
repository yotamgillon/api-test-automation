# api-test-automation

[![ci](https://github.com/yotamgillon/api-test-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/yotamgillon/api-test-automation/actions/workflows/ci.yml)

A small QA automation portfolio project. It contains a tiny orders service (FastAPI, in memory) with a one-page UI, a test suite for it (pytest + httpx for the API, Playwright for the browser), CI, HTML and coverage reports, and bug reports.

The service can switch on 5 deliberately seeded bugs with `BUGGY_MODE`. The same suite runs against the correct app (all green) and against the buggy app (it fails on the seeded bugs), which shows that the tests can actually catch defects.

- [TEST_PLAN.md](TEST_PLAN.md): scope, risks, levels, what is not covered, requirement-to-test traceability
- [docs/bug_reports/](docs/bug_reports/): one report per seeded bug, with real evidence
- [results/](results/): saved outputs of the before and after runs

## Run it in 3 commands
Needs Python 3.13 and make.

```
make install   # virtualenv, pinned dependencies, Chromium for Playwright
make test      # full suite (API + UI) against the correct app
make report    # same suite, plus results/report.html and coverage (terminal and results/htmlcov)
```

Other targets: `make run` (start the app on port 8000), `make test-buggy` (all seeded bugs on), `make test-each-bug` (one run per bug, writes `results/by_bug/`), `make demo` (the before and after runs with saved output), `make lint`.

## Test pyramid used, and why
| Level | Tests | Tool |
|---|---|---|
| API | 79 | pytest + httpx, real uvicorn server in a background thread |
| UI | 7 | Playwright (Python, Chromium, headless) |

The counts come from `results/test_counts.txt` (`pytest --collect-only -q` for `tests/api` and `tests/ui`).

Most checks sit at the API level because it is faster and a failure points to a clear cause. The UI level only covers what needs a browser: the form, the table, refreshing after a delete, and validation messages. There is no separate unit level because the logic of this small app is reachable only through its HTTP routes.

How the tests stay deterministic: order ids come from a counter that is reset before every test, there is no random or time-based data, no sleeps (Playwright `expect` auto-waits, timeout 2000 ms), a fresh browser context per test, and no dependence on test order or on the internet. The buggy run was done twice and the two lists of failing test ids were identical.

## Before and after
Correct app (`make test`, output in `results/correct_run.txt`): **86 passed**.
All bugs on (`make test-buggy`, output in `results/buggy_run.txt`): **34 failed, 52 passed**.

`results/buggy_run.txt` ends with a `make: *** [test-buggy] Error 1` line on purpose. `make test-buggy` exits with an error because tests fail, and that is the expected result of this run. I kept the raw output unedited.

This demonstration shows that the tests work as designed on bugs I seeded myself. It does not show that they would find unknown bugs.

Which tests fail on which bug. Each bug was switched on alone (`BUGGY_MODE=BUG-00X`, `make test-each-bug`, ids in `results/by_bug/`):

| Bug | What is wrong | Failing tests | Count |
|---|---|---|---|
| BUG-001 | Zero and negative quantity accepted | quantity `minus-one` and `zero` (create and update), `test_bug001_negative_quantity_is_rejected_and_not_stored`, error-schema `422-quantity`, UI `quantity-0` | 7 |
| BUG-002 | Missing order returns 200 instead of 404 | `test_bug002_get_missing_order_returns_404`, `test_delete_then_get_returns_404`, error-schema `404-get`, `test_delete_returns_204_and_removes_only_that_order` | 4 |
| BUG-003 | List drops the last order | `test_bug003_list_returns_every_created_order` (3 cases), UI `test_create_order_through_form_shows_it_in_table` | 4 |
| BUG-004 | Invalid status transitions accepted | 15 forbidden-transition cases, `test_bug004_new_order_cannot_jump_straight_to_delivered`, `test_conflict_response_matches_error_schema` | 17 |
| BUG-005 | UI table not refreshed after delete | UI `test_bug005_delete_removes_row_without_page_reload` | 1 |
| BUG-003 + BUG-005 | Fails with either bug alone | UI `test_create_two_orders_delete_one_keeps_the_other` | 1 |
| **Total** | | | **34** |

The totals match: 7 + 4 + 4 + 17 + 1 + 1 = 34, and the union of the five per-bug files equals the 34 failures of the all-bugs run. BUG-002 and BUG-004 are not visible in the UI, so only API tests catch them. The failing tests are meant to be read together with the bug reports in `docs/bug_reports/`.

## Coverage
Measured with pytest-cov on the `app/` package over the full suite (API and UI), correct app, with branch coverage on (`make report`; output saved in `results/coverage.txt` and `results/coverage.json`):

| Measure | Result |
|---|---|
| Line coverage | 96.6 percent (115 of 119 statements) |
| Branch coverage | 86.7 percent (26 of 30 branches) |
| Combined figure printed by coverage.py (lines and branches together) | 94.6 percent (shown as 95 in the terminal table) |

What is not covered: the 4 uncovered lines (`app/main.py` lines 37, 54, 89, 99) and the 4 uncovered branches (the same four places) are all buggy-mode code, which only runs when `BUGGY_MODE` is set. Everything else in `app/` is covered. Coverage was measured only on the correct run. I did not add tests only to raise these numbers; the one added late (generated id versus client-chosen id) covers a real edge case in `app/store.py`.

The JavaScript inside `app/static/index.html` is not measured by coverage. It is exercised by the UI tests, but there is no number for it.

## CI
`.github/workflows/ci.yml` runs on every push: ruff, API tests, `playwright install --with-deps chromium`, UI tests (headless), and uploads the HTML reports as an artifact (`if: always()`). It uses Python 3.13, the same minor version as local development. The runner is pinned to `ubuntu-24.04`. One run on GitHub passed (run 38963384607). It tested Chromium only, and a single run is not a stability record.

## Limitations
- A small in-memory demo service, not a real product. There is no database, authentication or persistence.
- The tests were written for this demo system and its own spec (see TEST_PLAN.md); they are not a general test library.
- `/_reset` is a test-only endpoint. It exists only when `ENABLE_TEST_ENDPOINTS=1` is set and returns 404 otherwise.
- The page has a `data-loaded` attribute that exists only so tests can wait for the first load. The server also renders `data-buggy` into the page for the seeded UI bug.
- Only Chromium is tested. No cross-browser, performance, security, concurrency or accessibility testing (see TEST_PLAN.md).
- Only the 8 top-level dependencies are pinned; their sub-dependencies are not.
- The seeded bugs were written by me together with the tests that catch them, so the before and after demonstration shows the tests work as designed, not that they would find unknown bugs.
- CI: one GitHub Actions run passed (run 38963384607) on `ubuntu-24.04`, Chromium only. A single run is not a stability record.
