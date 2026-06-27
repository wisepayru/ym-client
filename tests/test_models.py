"""Unit tests for ym_client.models.

Two concerns: (1) the parsing edge cases that are easy to regress -- the Yandex
date formats, tolerance of missing optionals and unknown keys; (2) a
contract-drift guard that validates every response model against its
captured/spec-derived fixture, so the client and the YM API can't silently
diverge (see tests/fixtures/README.md for provenance).
"""

import datetime

import pytest

from ym_client.models import CalculateTariffsResponse, OrderResponse
from ym_client.models.generic import GenericErrorResponse, GenericSuccessResponse
from ym_client.models.get_order import Dates, Order


# --- date parsing ----------------------------------------------------------

def test_order_parses_yandex_datetime():
    order = Order.model_validate({
        "id": 1,
        "creationDate": "08-06-2026 23:40:32",
        "updatedAt": "08-06-2026 23:40:48",
    })
    assert order.creationDate == datetime.datetime(2026, 6, 8, 23, 40, 32)
    assert order.updatedAt == datetime.datetime(2026, 6, 8, 23, 40, 48)


def test_dates_parses_yandex_date_only():
    dates = Dates.model_validate({"fromDate": "08-06-2026", "toDate": "09-06-2026"})
    assert dates.fromDate == datetime.date(2026, 6, 8)
    assert dates.toDate == datetime.date(2026, 6, 9)


def test_invalid_date_raises():
    with pytest.raises(ValueError):
        Order.model_validate({"creationDate": "2026/06/08"})


# --- tolerance of missing optionals and unknown keys -----------------------

def test_order_response_tolerates_missing_optionals():
    # Everything is optional: an empty order body must validate.
    parsed = OrderResponse.model_validate({"order": {}})
    assert parsed.order.id is None
    assert parsed.order.items is None


def test_models_ignore_unknown_keys(load_fixture):
    # The captured payload carries fields beyond the model (buyer.email,
    # sourcePlatform). Pydantic ignores extras by default -- assert it stays so.
    body = load_fixture("orders/order_created.json")
    assert "sourcePlatform" in body["order"]
    assert "email" in body["order"]["buyer"]
    parsed = OrderResponse.model_validate(body)
    assert parsed.order.buyer.lastName == "Долгов"
    assert not hasattr(parsed.order, "sourcePlatform")


# --- captured getOrder payloads --------------------------------------------

def test_order_created_capture(load_fixture):
    parsed = OrderResponse.model_validate(load_fixture("orders/order_created.json"))
    assert parsed.order.id == 57962644480
    assert parsed.order.externalOrderId == "57962644480"
    assert parsed.order.delivery.type == "DIGITAL"
    assert parsed.order.items[0].offerId == "apple-giftcard-500-try"
    assert parsed.order.delivery.dates.fromDate == datetime.date(2026, 6, 8)


def test_order_status_updated_capture(load_fixture):
    parsed = OrderResponse.model_validate(load_fixture("orders/order_status_updated.json"))
    assert parsed.order.status == "DELIVERY"
    assert parsed.order.substatus == "DELIVERY_SERVICE_RECEIVED"
    assert parsed.order.updatedAt == datetime.datetime(2026, 6, 13, 13, 21, 54)


# --- calculateTariffs nested parsing ---------------------------------------

def test_calculate_tariffs_nested(load_fixture):
    parsed = CalculateTariffsResponse.model_validate(
        load_fixture("tariffs/calculate_success.json"))
    offer = parsed.result.offers[0]
    assert offer.offer.categoryId == 1
    assert len(offer.tariffs) == 2
    # parameters is optional on a tariff
    assert offer.tariffs[0].parameters[0].name == "value"
    assert offer.tariffs[1].parameters is None


# --- contract-drift guard --------------------------------------------------

# Each response model must parse the captured/spec-derived body for its
# endpoint. If the YM API changes a response shape, regenerate the fixture and
# this flags the divergence.
RESPONSE_CONTRACTS = [
    ("orders/order_created.json", OrderResponse),
    ("orders/order_status_updated.json", OrderResponse),
    ("tariffs/calculate_success.json", CalculateTariffsResponse),
    ("generic/success.json", GenericSuccessResponse),
    ("errors/error_response.json", GenericErrorResponse),
    ("tariffs/calculate_error.json", GenericErrorResponse),
]


@pytest.mark.parametrize("fixture, model", RESPONSE_CONTRACTS, ids=[c[0] for c in RESPONSE_CONTRACTS])
def test_response_model_matches_fixture(load_fixture, fixture, model):
    model.model_validate(load_fixture(fixture))
