# Test fixtures

Response/request bodies the client must parse or build, used by
`tests/test_client.py` and `tests/test_models.py`, from three sources:

## Real captures from qa (from ym-api's OpenSearch request logs)

Captured verbatim from the live Yandex Market Partner API via ym-api's
request-logging middleware, and shared from `ym-api/tests/fixtures/orders/` so
the client and its consumer can't silently diverge on the `getOrder` contract:

- `orders/order_created.json` — `GET .../orders/{orderId}` 200 (numeric
  `externalOrderId`; carries fields beyond the model such as `buyer.email` and
  `sourcePlatform`, which exercises the models' tolerance of unknown keys).
- `orders/order_status_updated.json` — `GET .../orders/{orderId}` 200 (a later
  status, `DELIVERY`).
## A production record

Not shared with ym-api:

- `errors/api_disabled.json` — the 403 body `GET .../orders/{orderId}` answered
  in production on 2026-09-26 for a store whose API Market had switched off
  (`DISABLED_BY_INACTIVITY`), as ym-api's log recorded it; the campaign id was
  masked in that record and stays `<n>` here. The `getBusinessOrders` 403 test
  uses it to fix how the client surfaces a 403; that method's own answer for a
  switched-off store has not been seen.

## Documentation examples (copied from the official Yandex Market Partner API docs)

Taken verbatim from the examples on
<https://yandex.ru/dev/market/partner-api/doc/ru/reference/orders/getBusinessOrders>,
so the values are the documentation's placeholders (`"example"`, `0`, `0.5`,
the first value of each enum).

- `orders/business_orders.json` — `POST /v1/businesses/{businessId}/orders` 200,
  `BusinessOrdersResponse`: the `BusinessOrderDTO` entity example as the one
  element of `orders`, and the `PackagingForwardScrollingPagerDTO` entity example
  as `paging`. The page's example of the whole 200 body is not used: it cuts
  nesting short with `null` array elements (`"instances": [null]`) that the
  documented schema does not allow.
- `errors/api_error_response.json` — the `ApiErrorResponse` entity example the
  page gives for its 400/401/403/404/420/500 bodies (`status: OK` beside
  `errors[]`, as documented). Parses into `GenericErrorResponse`.

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
