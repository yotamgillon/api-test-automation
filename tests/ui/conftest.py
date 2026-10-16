"""Playwright fixtures (plain sync API, no pytest-playwright).

One browser per session, a fresh context and page per test. Depending on `client`
resets the server state before every test.
"""

import pytest
from playwright.sync_api import expect, sync_playwright

# Short auto-wait so a failing assertion (for example in BUGGY_MODE) fails fast.
TIMEOUT_MS = 2000
expect.set_options(timeout=TIMEOUT_MS)


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser, client, base_url):
    context = browser.new_context(base_url=base_url)
    context.set_default_timeout(TIMEOUT_MS)
    page = context.new_page()
    page.goto("/")
    # The page marks itself loaded after its first fetch of the order list.
    expect(page.get_by_test_id("app")).to_have_attribute("data-loaded", "true")
    yield page
    context.close()
