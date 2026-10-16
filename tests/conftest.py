"""Shared fixtures.

The app runs inside the pytest process on a background thread (uvicorn.Server), so
coverage measures the real app code. Readiness is signalled by an Event that is set
right after uvicorn finishes its own startup (server.started becomes True).
"""

import asyncio
import os
import socket
import threading

import httpx
import pytest
import uvicorn

from app.main import app

STARTUP_TIMEOUT_S = 10

# Valid way to reach each status starting from a freshly created ("new") order.
PATH_TO_STATUS = {
    "new": [],
    "paid": ["paid"],
    "shipped": ["paid", "shipped"],
    "delivered": ["paid", "shipped", "delivered"],
    "cancelled": ["cancelled"],
}


class ReadyServer(uvicorn.Server):
    def __init__(self, config: uvicorn.Config) -> None:
        super().__init__(config)
        self.ready = threading.Event()

    async def startup(self, sockets=None) -> None:
        await super().startup(sockets=sockets)
        self.ready.set()


@pytest.fixture(scope="session")
def base_url():
    os.environ["ENABLE_TEST_ENDPOINTS"] = "1"
    # Bind the port ourselves so there is no free-port race and no fixed port.
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = ReadyServer(uvicorn.Config(app, log_level="warning"))
    thread = threading.Thread(target=lambda: asyncio.run(server.serve(sockets=[sock])), daemon=True)
    thread.start()
    if not server.ready.wait(STARTUP_TIMEOUT_S):
        raise RuntimeError("test server did not start")
    assert server.started
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(STARTUP_TIMEOUT_S)
    sock.close()


@pytest.fixture
def client(base_url):
    """HTTP client against a server that has just been reset (clean state per test)."""
    with httpx.Client(base_url=base_url, timeout=5) as c:
        assert c.post("/_reset").status_code == 204
        yield c


@pytest.fixture
def make_order(client):
    """Factory: creates a valid order (overridable fields) and returns its JSON."""

    def _make(**overrides):
        payload = {"customer": "Alice", "item": "Widget", "quantity": 1, **overrides}
        response = client.post("/orders", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def order_in_status(client, make_order):
    """Factory: creates an order and moves it to `status` using only valid transitions."""

    def _make(status: str):
        order = make_order()
        for step in PATH_TO_STATUS[status]:
            response = client.put(f"/orders/{order['id']}", json={"status": step})
            assert response.status_code == 200, response.text
        return order["id"]

    return _make
