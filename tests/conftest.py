"""Shared fixtures for the ym-client test suite.

No network is touched: ``mock_ym`` swaps ``httpx.AsyncClient`` for one wired to
an in-memory ``httpx.MockTransport``, so every request the client builds is
served by a local handler and captured for assertions.
"""

import json
from pathlib import Path

import httpx
import pytest

import ym_client.client as client_mod

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    """Load a JSON fixture body, e.g. ``load_fixture("orders/order_created.json")``."""
    def _load(relpath: str):
        with (FIXTURES_DIR / relpath).open(encoding="utf-8") as fh:
            return json.load(fh)
    return _load


class _MockYM:
    """Controller for the mocked transport.

    Configure the response with ``respond_json(...)`` / ``respond(...)`` /
    ``fail(...)``; inspect what the client sent via ``last_request`` (an
    ``httpx.Request`` -- read ``.method``, ``.url``, ``.headers``, and
    ``json.loads(.content)`` for the body).
    """

    def __init__(self):
        self.requests: list[httpx.Request] = []
        self._responder = None

    def respond(self, response: httpx.Response):
        self._responder = lambda request: response

    def respond_json(self, body, status_code: int = 200):
        self._responder = lambda request: httpx.Response(status_code, json=body)

    def fail(self, exc: Exception):
        """Make every send raise ``exc`` (e.g. ``httpx.ConnectError`` to drive retries)."""
        def _raise(request):
            raise exc
        self._responder = _raise

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self._responder is None:
            return httpx.Response(200, json={})
        return self._responder(request)

    @property
    def last_request(self) -> httpx.Request:
        assert self.requests, "no request was made"
        return self.requests[-1]


@pytest.fixture
def mock_ym(monkeypatch):
    """Route the client's httpx.AsyncClient through an in-memory MockTransport."""
    controller = _MockYM()
    real_async_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(controller._handle)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(client_mod.httpx, "AsyncClient", factory)
    return controller


@pytest.fixture
def fast_retry(monkeypatch):
    """Zero the 2s fixed wait on ``Client._request`` so retry tests run instantly.

    Leaves the stop condition (5 attempts) and retried exception set intact.
    """
    from tenacity import wait_fixed
    monkeypatch.setattr(client_mod.Client._request.retry, "wait", wait_fixed(0))
