from ym_client import Client
from ym_client.models import (
    OrderResponse,
    GenericSuccessResponse,
    GenericErrorResponse,
    CalculateTariffsResponse,
)


def test_client_import():
    assert Client is not None


def test_models_import():
    assert OrderResponse is not None
    assert GenericSuccessResponse is not None
    assert GenericErrorResponse is not None
    assert CalculateTariffsResponse is not None


def test_client_requires_token():
    try:
        Client(campaignId=123, token=None)
        assert False, "Expected exception not raised"
    except Exception:
        pass


def test_client_requires_campaign_id():
    try:
        Client(campaignId=None, token="test-token")
        assert False, "Expected exception not raised"
    except Exception:
        pass
