"""BUG-005: the table is not refreshed after a delete.

Run from the repo root: .venv/bin/python docs/bug_reports/repro/BUG-005.py
Starts the app itself with BUGGY_MODE=BUG-005, drives the page with Playwright and saves
a screenshot of the table after the delete (before the reload).
"""

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SHOT = ROOT / "docs/bug_reports/img/BUG-005_after_delete.png"
PORT = 8805
BASE = f"http://127.0.0.1:{PORT}"


def post(path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        BASE + path, method="POST", data=data, headers={"Content-Type": "application/json"}
    )
    return urllib.request.urlopen(req).status


def wait_until_up():
    for _ in range(50):
        try:
            urllib.request.urlopen(BASE + "/orders")
            return
        except OSError:
            subprocess.run(["sleep", "0.2"])
    raise RuntimeError("app did not start")


env = {**os.environ, "BUGGY_MODE": "BUG-005", "ENABLE_TEST_ENDPOINTS": "1"}
app = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--port",
        str(PORT),
        "--log-level",
        "warning",
    ],
    cwd=ROOT,
    env=env,
)
try:
    wait_until_up()
    print(f"# Reproduction run with BUGGY_MODE=BUG-005 against {BASE}")
    post("/_reset")
    post("/orders", {"customer": "First", "item": "Pen", "quantity": 1})
    post("/orders", {"customer": "Second", "item": "Ink", "quantity": 1})
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(base_url=BASE)
        page.goto("/")
        expect(page.get_by_test_id("app")).to_have_attribute("data-loaded", "true")
        print(
            "step 1: page opened, data-buggy =",
            page.get_by_test_id("app").get_attribute("data-buggy"),
        )
        row = page.get_by_test_id("order-row-ORD-0001")
        print("step 2: rows before delete (ORD-0001 visible):", row.count() == 1)
        with page.expect_response(lambda r: r.request.method == "DELETE") as response:
            page.get_by_test_id("delete-ORD-0001").click()
        print("step 3: clicked Delete, server answered HTTP", response.value.status)
        print("step 4: ORD-0001 rows still in table, no reload:", row.count())
        page.get_by_test_id("orders-table").screenshot(path=str(SHOT))
        print("step 4b: screenshot of the table saved to", SHOT.relative_to(ROOT))
        page.reload()
        expect(page.get_by_test_id("app")).to_have_attribute("data-loaded", "true")
        print("step 5: ORD-0001 rows after manual reload:", row.count())
        browser.close()
finally:
    app.terminate()
    app.wait()
