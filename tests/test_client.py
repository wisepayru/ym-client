"""Behavioral tests for ym_client.Client.

Every request is served by an in-memory httpx.MockTransport (see conftest's
``mock_ym``); no network is touched. We assert, per method: the outgoing
request (verb, path, body), that the ``headers=`` trace-propagation param (#10)
reaches the wire, and that the response parses into the right model -- including
the success/error dispatch on the response body.
"""

import json
from uuid import UUID

import httpx
import pytest
import tenacity

from ym_client import Client
from ym_client.models import CalculateTariffsResponse, OrderResponse
from ym_client.models.generic import GenericErrorResponse, GenericSuccessResponse

SCHEMA = "https"
URL = "api.partner.market.yandex.ru"
BASE_URL = f"{SCHEMA}://{URL}"
TOKEN = "test-market-token"
CAMPAIGN_ID = 49152127
ORDER_ID = 57962644480
TRACE = {"X-Trace-Id": "trace-123", "X-Request-Id": "req-456"}

EXTERNAL_ID = UUID("ce3bac49-e15d-4d1c-9e41-8d9a5fb8fc52")
DIGITAL_ITEMS = [
    {
        "id": 1124062679,
        "codes": ["AAAA-BBBB-CCCC", "DDDD-EEEE-FFFF"],
        "slip": "Activate at https://example.test/redeem",
        "activate_till": "2026-12-31",
    }
]
OFFERS = [{"categoryId": 1, "price": 1299.0, "quantity": 4}]


def make_client() -> Client:
    return Client(schema=SCHEMA, url=URL, campaignId=CAMPAIGN_ID, token=TOKEN)


# --- auth / base-url -------------------------------------------------------

async def test_auth_header_and_base_url(mock_ym, load_fixture):
    mock_ym.respond_json(load_fixture("orders/order_created.json"))
    async with make_client() as client:
        await client.getOrder(ORDER_ID)

    req = mock_ym.last_request
    assert req.headers["Api-Key"] == TOKEN
    assert req.headers["User-Agent"].startswith("wisepay-ym-client/")
    assert str(req.url) == f"{BASE_URL}/v2/campaigns/{CAMPAIGN_ID}/orders/{ORDER_ID}"


async def test_uninitialized_client_raises():
    # Calling a method without `async with` leaves self._client None.
    client = make_client()
    with pytest.raises(RuntimeError, match="not initialized"):
        await client.getOrder(ORDER_ID)


# --- request building + response parsing, per method -----------------------

async def test_get_order(mock_ym, load_fixture):
    body = load_fixture("orders/order_created.json")
    mock_ym.respond_json(body)
    async with make_client() as client:
        req, resp, parsed = await client.getOrder(ORDER_ID)

    sent = mock_ym.last_request
    assert sent.method == "GET"
    assert sent.url.path == f"/v2/campaigns/{CAMPAIGN_ID}/orders/{ORDER_ID}"
    assert sent.content == b""  # no request body
    assert isinstance(parsed, OrderResponse)
    assert parsed.order.id == body["order"]["id"]
    assert parsed.order.status == "PROCESSING"


async def test_set_order_external_id(mock_ym, load_fixture):
    mock_ym.respond_json(load_fixture("generic/success.json"))
    async with make_client() as client:
        req, resp, parsed = await client.setOrderExternalId(ORDER_ID, EXTERNAL_ID)

    sent = mock_ym.last_request
    assert sent.method == "POST"
    assert sent.url.path == f"/v2/campaigns/{CAMPAIGN_ID}/orders/{ORDER_ID}/external-id"
    # the UUID is serialized to its string form in the body
    assert json.loads(sent.content) == {"externalOrderId": str(EXTERNAL_ID)}
    assert isinstance(parsed, GenericSuccessResponse)
    assert parsed.status == "OK"


async def test_deliver_digital_goods(mock_ym, load_fixture):
    mock_ym.respond_json(load_fixture("generic/success.json"))
    async with make_client() as client:
        req, resp, parsed = await client.deliverDigitalGoods(ORDER_ID, DIGITAL_ITEMS)

    sent = mock_ym.last_request
    assert sent.method == "POST"
    assert sent.url.path == f"/v2/campaigns/{CAMPAIGN_ID}/orders/{ORDER_ID}/deliverDigitalGoods"
    # items are forwarded verbatim under an "items" key
    assert json.loads(sent.content) == {"items": DIGITAL_ITEMS}
    assert isinstance(parsed, GenericSuccessResponse)
    assert parsed.status == "OK"


async def test_calculate_tariffs(mock_ym, load_fixture):
    body = load_fixture("tariffs/calculate_success.json")
    mock_ym.respond_json(body)
    async with make_client() as client:
        req, resp, parsed = await client.calculateTariffs(OFFERS)

    sent = mock_ym.last_request
    assert sent.method == "POST"
    assert sent.url.path == "/v2/tariffs/calculate"
    body_sent = json.loads(sent.content)
    assert body_sent["parameters"] == {"campaignId": CAMPAIGN_ID}
    # each offer is normalized: passed fields kept, omitted dimensions default to 1
    assert body_sent["offers"] == [
        {
            "categoryId": 1,
            "price": 1299.0,
            "quantity": 4,
            "length": 1,
            "width": 1,
            "height": 1,
            "weight": 1,
        }
    ]
    assert isinstance(parsed, CalculateTariffsResponse)
    assert parsed.status == "OK"
    tariffs = parsed.result.offers[0].tariffs
    assert tariffs[0].type == "AGENCY_COMMISSION"
    assert tariffs[0].parameters[0].value == "5"
    assert tariffs[1].type == "FEE"
    assert tariffs[1].amount == 458.67


async def test_calculate_tariffs_offer_defaults_can_be_overridden(mock_ym, load_fixture):
    mock_ym.respond_json(load_fixture("tariffs/calculate_success.json"))
    offers = [{"categoryId": 7, "price": 500, "quantity": 2,
               "length": 10, "width": 20, "height": 30, "weight": 1.5}]
    async with make_client() as client:
        await client.calculateTariffs(offers)

    sent = json.loads(mock_ym.last_request.content)
    assert sent["offers"][0] == {
        "categoryId": 7, "price": 500, "quantity": 2,
        "length": 10, "width": 20, "height": 30, "weight": 1.5,
    }


# --- error dispatch (business errors arrive as HTTP 200) -------------------

async def test_get_order_error_dispatch(mock_ym, load_fixture):
    mock_ym.respond_json(load_fixture("errors/error_response.json"))
    async with make_client() as client:
        req, resp, parsed = await client.getOrder(ORDER_ID)

    assert isinstance(parsed, GenericErrorResponse)
    assert parsed.status == "ERROR"
    assert parsed.errors[0].code == "NOT_FOUND"


async def test_set_order_external_id_error_dispatch(mock_ym, load_fixture):
    mock_ym.respond_json(load_fixture("errors/error_response.json"))
    async with make_client() as client:
        _, _, parsed = await client.setOrderExternalId(ORDER_ID, EXTERNAL_ID)
    assert isinstance(parsed, GenericErrorResponse)


async def test_deliver_digital_goods_error_dispatch(mock_ym, load_fixture):
    mock_ym.respond_json(load_fixture("errors/error_response.json"))
    async with make_client() as client:
        _, _, parsed = await client.deliverDigitalGoods(ORDER_ID, DIGITAL_ITEMS)
    assert isinstance(parsed, GenericErrorResponse)


async def test_calculate_tariffs_error_dispatch(mock_ym, load_fixture):
    # calculateTariffs dispatches on status == "ERROR" as well as an errors key.
    mock_ym.respond_json(load_fixture("tariffs/calculate_error.json"))
    async with make_client() as client:
        _, _, parsed = await client.calculateTariffs(OFFERS)
    assert isinstance(parsed, GenericErrorResponse)
    assert parsed.status == "ERROR"


async def test_calculate_tariffs_status_error_without_errors_key(mock_ym):
    # A bare `status: ERROR` (no errors[]) must still dispatch to the error model.
    mock_ym.respond_json({"status": "ERROR"})
    async with make_client() as client:
        _, _, parsed = await client.calculateTariffs(OFFERS)
    assert isinstance(parsed, GenericErrorResponse)
    assert parsed.errors is None


# --- trace-header propagation (#10) across every method --------------------

# (id, fixture, coroutine factory) -- each method must forward headers= verbatim.
HEADER_CASES = [
    ("getOrder", "orders/order_created.json",
     lambda c, h: c.getOrder(ORDER_ID, headers=h)),
    ("setOrderExternalId", "generic/success.json",
     lambda c, h: c.setOrderExternalId(ORDER_ID, EXTERNAL_ID, headers=h)),
    ("deliverDigitalGoods", "generic/success.json",
     lambda c, h: c.deliverDigitalGoods(ORDER_ID, DIGITAL_ITEMS, headers=h)),
    ("calculateTariffs", "tariffs/calculate_success.json",
     lambda c, h: c.calculateTariffs(OFFERS, headers=h)),
]


@pytest.mark.parametrize("name, fixture, call", HEADER_CASES, ids=[c[0] for c in HEADER_CASES])
async def test_headers_propagated(mock_ym, load_fixture, name, fixture, call):
    mock_ym.respond_json(load_fixture(fixture))
    async with make_client() as client:
        await call(client, TRACE)

    sent = mock_ym.last_request
    for key, value in TRACE.items():
        assert sent.headers[key] == value
    # the static auth header is preserved alongside the per-request headers
    assert sent.headers["Api-Key"] == TOKEN


# --- retry / error surfacing -----------------------------------------------
# These assert the client's *current* behavior. The retry policy diverges from
# iris-client (no transient-5xx retry, no reraise=True) -- tracked in #15.

async def test_network_error_retries_then_raises_retryerror(mock_ym, fast_retry):
    # ConnectError is an httpx.RequestError -> retried up to 5 attempts. Without
    # reraise=True (#15) tenacity wraps the cause in a RetryError on exhaustion.
    mock_ym.fail(httpx.ConnectError("boom"))
    async with make_client() as client:
        with pytest.raises(tenacity.RetryError) as exc:
            await client.getOrder(ORDER_ID)
    assert isinstance(exc.value.last_attempt.exception(), httpx.ConnectError)
    assert len(mock_ym.requests) == 5


@pytest.mark.parametrize("status_code", [400, 403, 404, 422])
async def test_permanent_4xx_is_not_retried(mock_ym, fast_retry, status_code):
    # raise_for_status raises HTTPStatusError, which is not an httpx.RequestError,
    # so caller errors surface on the first attempt.
    mock_ym.respond_json({"detail": "nope"}, status_code=status_code)
    async with make_client() as client:
        with pytest.raises(httpx.HTTPStatusError) as exc:
            await client.getOrder(ORDER_ID)
    assert exc.value.response.status_code == status_code
    assert len(mock_ym.requests) == 1


@pytest.mark.xfail(strict=True, reason="#15: transient 5xx/429 should be retried like iris-client")
@pytest.mark.parametrize("status_code", [429, 502, 503, 504])
async def test_transient_status_is_retried(mock_ym, fast_retry, status_code):
    # Desired behavior (iris-client parity): transient server statuses are
    # retried up to 5 attempts. Currently they are not (HTTPStatusError is not
    # an httpx.RequestError), so this xfails until #15 is fixed.
    mock_ym.respond_json({"detail": "later"}, status_code=status_code)
    async with make_client() as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.getOrder(ORDER_ID)
    assert len(mock_ym.requests) == 5
