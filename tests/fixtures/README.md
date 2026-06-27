# Test fixtures

Response/request bodies the client must parse or build, used by
`tests/test_client.py` and `tests/test_models.py`. Two provenances:

## Real captures (from ym-api's OpenSearch request logs, env `qa`)

Captured verbatim from the live Yandex Market Partner API via ym-api's
request-logging middleware, and shared from `ym-api/tests/fixtures/orders/` so
the client and its consumer can't silently diverge on the `getOrder` contract:

- `orders/order_created.json` — `GET .../orders/{orderId}` 200 (numeric
  `externalOrderId`; carries fields beyond the model such as `buyer.email` and
  `sourcePlatform`, which exercises the models' tolerance of unknown keys).
- `orders/order_status_updated.json` — `GET .../orders/{orderId}` 200 (a later
  status, `DELIVERY`).

## Spec-derived (built from the official Yandex Market Partner API docs)

No real captures of these responses were available, so they are synthesized
from the documented schemas and reuse realistic ids/amounts seen in the
`getOrder` captures. Replace them with real captures if/when those become
available, and drop this note.

- `tariffs/calculate_success.json` — `POST /v2/tariffs/calculate` 200,
  `CalculateTariffsResponse`. Shape per
  <https://yandex.ru/dev/market/partner-api/doc/ru/reference/tariffs/calculateTariffs>
  (`status`, `result.offers[].{offer, tariffs[].{type, amount, currency,
  parameters[]}}`; `tariffs[].parameters` is optional and shown on one entry).
- `tariffs/calculate_error.json` — same endpoint, the documented business-error
  envelope (`status: ERROR` + `errors[]`), returned with HTTP 200. The client
  dispatches it to `GenericErrorResponse` via `status == 'ERROR'`.
- `generic/success.json` — `{"status": "OK"}`, the documented success body for
  `setOrderExternalId`
  (<https://yandex.ru/dev/market/partner-api/doc/ru/reference/orders/updateExternalOrderId>)
  and `deliverDigitalGoods`
  (<https://yandex.ru/dev/market/partner-api/doc/ru/reference/orders/provideOrderDigitalCodes>).
  Parses into `GenericSuccessResponse`.
- `errors/error_response.json` — the documented error envelope
  (`status: ERROR` + `errors[]`), returned with HTTP 200; the client dispatches
  it to `GenericErrorResponse` via the presence of the `errors` key. Used for
  the `getOrder` / `setOrderExternalId` / `deliverDigitalGoods` error paths.
