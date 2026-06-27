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
pip install git+https://github.com/wisepayru/ym-client.git@1.0.0
```

Released wheels/sdists are also attached to each
[GitHub Release](https://github.com/wisepayru/ym-client/releases).

Requires Python >= 3.14. Runtime deps: `httpx`, `pydantic`, `tenacity`.

## Usage

The client is an async context manager scoped to a single campaign. Every call
returns a `(httpx.Request, httpx.Response, parsed_model)` tuple, where the model
is either the success model or a `GenericErrorResponse` (see
[Behavior](#behavior)).

```python
from uuid import UUID
from ym_client import Client
from ym_client.models import OrderResponse

async def example():
    async with Client(campaignId=49152127, token="...") as client:
        # fetch an order
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

`Client(schema='https', url='api.partner.market.yandex.ru', campaignId=..., token=...)`
— `schema` and `url` default to production; `campaignId` and `token` are required.

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
| `setOrderExternalId(orderId, externalOrderId, headers=None)` | `POST v2/campaigns/{campaignId}/orders/{orderId}/external-id` | `GenericSuccessResponse` |
| `deliverDigitalGoods(orderId, items, headers=None)` | `POST v2/campaigns/{campaignId}/orders/{orderId}/deliverDigitalGoods` | `GenericSuccessResponse` |
| `calculateTariffs(offers, headers=None)` | `POST v2/tariffs/calculate` | `CalculateTariffsResponse` |

`offers` is a list of dicts (`categoryId`, `price`, `quantity`, and optional
`length`/`width`/`height`/`weight`, each defaulting to `1`). Model definitions
live in [`ym_client/models/`](ym_client/models/).

## Behavior

- **Auth:** `Client(campaignId, token)` sends an `Api-Key: <token>` header and a
  `wisepay-ym-client/<version>` User-Agent on every request. Both `campaignId`
  and `token` are required.
- **Business errors are returned, not raised:** a response whose body carries
  `errors` (or `status: ERROR`, for `calculateTariffs`) is parsed into
  `GenericErrorResponse` and returned as the third tuple element. Dispatch on the
  returned type (e.g. `isinstance(result, OrderResponse)`).
- **HTTP errors:** non-2xx responses raise `httpx.HTTPStatusError` via
  `raise_for_status()`.
- **Retries:** requests are retried up to 5 times (fixed 2s wait) on transport
  errors (connect/read/timeout) and transient server statuses (`429`, `502`,
  `503`, `504`). Permanent 4xx (e.g. `403`, `404`) raise immediately. On
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
