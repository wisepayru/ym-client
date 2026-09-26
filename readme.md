# ym-client

Async Python client for the
[Yandex Market Partner API](https://yandex.ru/dev/market/partner-api/doc/ru/).
Wraps the order and tariff endpoints in an `httpx`-based client that returns
parsed Pydantic models, with built-in retries and trace-header propagation.

Its request/response models track the Yandex Market API; see [`tests/`](tests/)
for the contract-drift guard and [`tests/fixtures/README.md`](tests/fixtures/README.md)
for fixture provenance.

## Installation

Pinned to a release tag (the supported consumption path):

```bash
pip install git+https://github.com/wisepayru/ym-client.git@1.1.0
```

Released wheels/sdists are also attached to each
[GitHub Release](https://github.com/wisepayru/ym-client/releases).

Requires Python >= 3.14. Runtime deps: `httpx`, `pydantic`, `tenacity`.

## Usage

The client is an async context manager scoped to a single campaign, and to the
business (cabinet) that owns it for the business-level `getBusinessOrders`. Every
call returns a `(httpx.Request, httpx.Response, parsed_model)` tuple, where the
model is either the success model or a `GenericErrorResponse` (see
[Behavior](#behavior)).

```python
from uuid import UUID
from ym_client import Client
from ym_client.models import BusinessOrdersResponse, OrderResponse

async def example(business_id: int):
    async with Client(campaignId=49152127, businessId=business_id, token="...") as client:
        # fetch orders by id (up to 50 per call)
        req, resp, result = await client.getBusinessOrders([57962644480])
        if isinstance(result, BusinessOrdersResponse):
            for order in result.orders:
                print(order.orderId, order.status)

        # fetch an order through the campaign-level method
        req, resp, result = await client.getOrder(57962644480)
        if isinstance(result, OrderResponse):
            print(result.order.status)  # -> "PROCESSING"

        # set the external (internal) order id
        await client.setOrderExternalId(
            57962644480, UUID("ce3bac49-e15d-4d1c-9e41-8d9a5fb8fc52")
        )

        # deliver digital codes
        await client.deliverDigitalGoods(57962644480, items=[
            {
                "id": 1124062679,
                "codes": ["AAAA-BBBB-CCCC"],
                "slip": "Activation instructions...",
                "activate_till": "2026-12-31",
            },
        ])

        # calculate tariffs for a batch of offers (up to 200)
        _, _, tariffs = await client.calculateTariffs([
            {"categoryId": 1, "price": 1299, "quantity": 4},
        ])
        print(tariffs.result.offers[0].tariffs)
```

`Client(schema='https', url='api.partner.market.yandex.ru', campaignId=..., token=..., businessId=None)`
— `schema` and `url` default to production; `campaignId` and `token` are required.
`businessId` is needed only by `getBusinessOrders`, which raises `RuntimeError`
without it; `GET v2/campaigns` returns it as `business.id` of each campaign.

### Trace propagation

Every method takes an optional `headers=` dict that is merged onto the outgoing
request (the static `Api-Key`/User-Agent headers are preserved). Use it to
forward trace/correlation IDs:

```python
await client.getOrder(order_id, headers={"X-Trace-Id": trace_id})
```

## Methods

| Method | HTTP | Returns (or `GenericErrorResponse`) |
|---|---|---|
| `getOrder(orderId, headers=None)` | `GET v2/campaigns/{campaignId}/orders/{orderId}` | `OrderResponse` |
| `getBusinessOrders(orderIds=None, *, ..., pageToken=None, limit=None, headers=None)` | `POST v1/businesses/{businessId}/orders` | `BusinessOrdersResponse` |
| `setOrderExternalId(orderId, externalOrderId, headers=None)` | `POST v2/campaigns/{campaignId}/orders/{orderId}/external-id` | `GenericSuccessResponse` |
| `deliverDigitalGoods(orderId, items, headers=None)` | `POST v2/campaigns/{campaignId}/orders/{orderId}/deliverDigitalGoods` | `GenericSuccessResponse` |
| `calculateTariffs(offers, headers=None)` | `POST v2/tariffs/calculate` | `CalculateTariffsResponse` |

`offers` is a list of dicts (`categoryId`, `price`, `quantity`, and optional
`length`/`width`/`height`/`weight`, each defaulting to `1`). Model definitions
live in [`ym_client/models/`](ym_client/models/).

### getBusinessOrders

Yandex Market marks `getOrder` deprecated: unstable from 18 January 2027 and
switched off on 12 April 2027, with `getBusinessOrders` as its replacement.

- **Filters** are keyword arguments named as in the request body: `orderIds`
  (the only positional one), `externalOrderIds`, `programTypes`, `campaignIds`,
  `statuses`, `substatuses`, `dates` (an `OrderDatesFilterDTO`), `fake`,
  `waitingForCancellationApprove`, `sourcePlatforms`. A filter left as `None` is
  not sent. The body is validated by `GetBusinessOrdersRequest` before the
  request: every list takes at least one item, and `orderIds`,
  `externalOrderIds` and `campaignIds` at most 50; a list outside that range
  raises `pydantic.ValidationError` with no request made.
- **Paging:** up to `limit` orders per page (at most 50); pass
  `result.paging.nextPageToken` back as `pageToken` for the next page.
- **Dates window:** Market's documentation states that without date filters the
  method covers the last 30 days, and that one request spans at most 30 days.
  Whether that window also applies when orders are requested by `orderIds` is
  not documented.
- **Response shape** differs from `getOrder`: the id is `orderId`, not `id`;
  the update time is `updateDate`, not `updatedAt`; `creationDate` and
  `updateDate` are ISO 8601 with an offset and parse timezone-aware; amounts sit
  under `prices` as `{value, currencyId}`, per item for all its units together,
  in place of `price`, `buyerTotal` and the other totals; there is no `buyer`
  block (only `buyerType`), no `subsidies` list and no `taxSystem`.
- **An id that matches nothing:** the method's page documents a `404` for a
  missing resource (the path, the business or a campaign), but no error for an
  order id that matches no order, so such an id is expected to be missing from
  `orders`; this has not been checked against a live answer.
- **A switched-off API** answers `403`, which raises `httpx.HTTPStatusError`
  without a retry, as for every method. The documentation names the business
  level's own case: when every store in the business is switched off, the
  message is `API for business {businessId} disabled because it has only
  disabled partners`.

## Behavior

- **Auth:** `Client(campaignId, token)` sends an `Api-Key: <token>` header and a
  `wisepay-ym-client/<version>` User-Agent on every request. Both `campaignId`
  and `token` are required.
- **Business errors are returned, not raised:** a response whose body carries
  a non-empty `errors` (or `status: ERROR`, for `calculateTariffs`) is parsed into
  `GenericErrorResponse` and returned as the third tuple element. Dispatch on the
  returned type (e.g. `isinstance(result, OrderResponse)`).
- **HTTP errors:** non-2xx responses raise `httpx.HTTPStatusError` via
  `raise_for_status()`.
- **Retries:** requests are retried up to 5 times (fixed 2s wait) on transport
  errors (connect/read/timeout), Market's rate limit (`420`, and `429` from
  anything in between) and transient server statuses (`502`, `503`, `504`).
  Permanent 4xx (e.g. `403`, `404`) raise immediately. On
  exhaustion the underlying `httpx` exception is re-raised (not wrapped in
  `tenacity.RetryError`).

## Development

```bash
python3.14 -m venv .venv
.venv/bin/pip install -e . -r requirements-test.txt
.venv/bin/ruff check .
.venv/bin/pytest
```

CI (lint + tests) runs on every push/PR via
[`.github/workflows/test.yml`](.github/workflows/test.yml); each published
GitHub Release builds and attaches a wheel + sdist via
[`.github/workflows/release-artifacts.yml`](.github/workflows/release-artifacts.yml).

## License

[MPL-2.0](LICENSE).
