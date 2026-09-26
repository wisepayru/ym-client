import httpx
from importlib.metadata import version, PackageNotFoundError
from typing import Dict, List, Any, Optional, Tuple, Union
from uuid import UUID
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception,
    retry_if_exception_type,
)
from pydantic import BaseModel
from .models import (
    OrderResponse,
    CalculateTariffsResponse,
    BusinessOrdersResponse,
    GetBusinessOrdersRequest,
    OrderDatesFilterDTO,
)
from .models.generic import GenericSuccessResponse, GenericErrorResponse

try:
    _version = version("ym-client")
except PackageNotFoundError:
    _version = "dev"

_USER_AGENT = f"wisepay-ym-client/{_version}"

# Transient server-side statuses worth retrying: Market's rate limit, which it
# answers with 420 (its limits page), 429 from anything in between, and
# gateway/upstream hiccups. Other 4xx are caller errors and are not retried.
_RETRYABLE_STATUS_CODES = frozenset({420, 429, 502, 503, 504})


def _is_retryable_status_error(exc: BaseException) -> bool:
    return (
        isinstance(exc, httpx.HTTPStatusError)
        and exc.response.status_code in _RETRYABLE_STATUS_CODES
    )


class Client:
    def __init__(
            self,
            schema: str = 'https',
            url: str = 'api.partner.market.yandex.ru',
            campaignId: int = None,
            token: str = None,
            businessId: int = None):
        if token is None:
            raise Exception("Yandex Market API token was not provided. In order to init a Y.Market client, please provide a token.")
        if campaignId is None:
            raise Exception("Yandex Market campaignId was not provided.")

        self.base_url = f'{schema}://{url}'
        self.campaignId = campaignId
        self.businessId = businessId
        self._token = token
        self._headers = {
            "User-Agent": _USER_AGENT,
            "Api-Key": self._token
        }
        self._client = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=httpx.Timeout(10.0, connect=5.0)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(2),
        # Retry transport errors (connect/read/timeout) and transient server
        # statuses (420/429/502/503/504, #15). Permanent 4xx (e.g. 403/404) raise
        # immediately.
        retry=(
            retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
            | retry_if_exception(_is_retryable_status_error)
        ),
        # Re-raise the underlying httpx error on exhaustion instead of wrapping
        # it in tenacity.RetryError, so consumers can catch httpx exceptions
        # directly (#15).
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        url: str,
        success_model: type[BaseModel],
        extra_headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Tuple[httpx.Request, httpx.Response, Union[BaseModel, GenericErrorResponse]]:
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with Client(...)'.")
        if extra_headers:
            kwargs["headers"] = {**kwargs.pop("headers", {}), **extra_headers}
        req = self._client.build_request(method, url, **kwargs)
        resp = await self._client.send(req)
        resp.raise_for_status()
        data = resp.json()
        # YM signals business errors in the body (a non-empty `errors` list, or
        # `status: ERROR` for tariffs) while still returning HTTP 200; an
        # `errors` that is null or empty is not an error.
        if data.get('errors') or data.get('status') == 'ERROR':
            return req, resp, GenericErrorResponse.model_validate(data)
        return req, resp, success_model.model_validate(data)

    async def getOrder(
        self,
        orderId: int,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[httpx.Request, httpx.Response, Union[OrderResponse, GenericErrorResponse]]:
        """
        Retrieve an order by its ID.
        https://yandex.ru/dev/market/partner-api/doc/ru/reference/orders/getOrder
        """
        endpoint = f'v2/campaigns/{self.campaignId}/orders/{orderId}'
        return await self._request('GET', endpoint, OrderResponse, extra_headers=headers)

    async def getBusinessOrders(
        self,
        orderIds: Optional[List[int]] = None,
        *,
        externalOrderIds: Optional[List[str]] = None,
        programTypes: Optional[List[str]] = None,
        campaignIds: Optional[List[int]] = None,
        statuses: Optional[List[str]] = None,
        substatuses: Optional[List[str]] = None,
        dates: Optional[OrderDatesFilterDTO] = None,
        fake: Optional[bool] = None,
        waitingForCancellationApprove: Optional[bool] = None,
        sourcePlatforms: Optional[List[str]] = None,
        pageToken: Optional[str] = None,
        limit: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[httpx.Request, httpx.Response, Union[BusinessOrdersResponse, GenericErrorResponse]]:
        """
        Retrieve the business's orders matching the given filters, one page at a time.
        Filters left as None are not sent; the body is validated against
        GetBusinessOrdersRequest before anything goes out, so a list of more than
        50 orderIds raises pydantic.ValidationError without a request.
        https://yandex.ru/dev/market/partner-api/doc/ru/reference/orders/getBusinessOrders
        """
        if self.businessId is None:
            raise RuntimeError("Yandex Market businessId was not provided.")
        endpoint = f'v1/businesses/{self.businessId}/orders'
        body = GetBusinessOrdersRequest(
            orderIds=orderIds,
            externalOrderIds=externalOrderIds,
            programTypes=programTypes,
            campaignIds=campaignIds,
            statuses=statuses,
            substatuses=substatuses,
            dates=dates,
            fake=fake,
            waitingForCancellationApprove=waitingForCancellationApprove,
            sourcePlatforms=sourcePlatforms,
        ).model_dump(mode='json', exclude_none=True)
        params = {
            key: value
            for key, value in (("pageToken", pageToken), ("limit", limit))
            if value is not None
        }
        return await self._request(
            'POST', endpoint, BusinessOrdersResponse, json=body, params=params, extra_headers=headers
        )

    async def deliverDigitalGoods(
        self,
        orderId: int,
        items: list,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[httpx.Request, httpx.Response, Union[GenericSuccessResponse, GenericErrorResponse]]:
        """
        Provide digital codes for an order.
        https://yandex.ru/dev/market/partner-api/doc/ru/reference/orders/provideOrderDigitalCodes
        """
        endpoint = f'v2/campaigns/{self.campaignId}/orders/{orderId}/deliverDigitalGoods'
        body = {"items": items}
        return await self._request('POST', endpoint, GenericSuccessResponse, json=body, extra_headers=headers)

    async def setOrderExternalId(
        self,
        orderId: int,
        externalOrderId: UUID,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[httpx.Request, httpx.Response, Union[GenericSuccessResponse, GenericErrorResponse]]:
        """
        Sets an external identifier for an order.
        https://yandex.ru/dev/market/partner-api/doc/ru/reference/orders/updateExternalOrderId
        """
        endpoint = f'v2/campaigns/{self.campaignId}/orders/{orderId}/external-id'
        body = {"externalOrderId": str(externalOrderId)}
        return await self._request('POST', endpoint, GenericSuccessResponse, json=body, extra_headers=headers)

    async def calculateTariffs(
        self,
        offers: List[Dict[str, Any]],
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[httpx.Request, httpx.Response, Union[CalculateTariffsResponse, GenericErrorResponse]]:
        """
        Calculate tariffs for a batch of offers (up to 200).
        Each offer dict must contain: categoryId, price, quantity, and optionally
        length, width, height, weight (all default to 1 if omitted).
        https://yandex.ru/dev/market/partner-api/doc/ru/reference/tariffs/calculateTariffs
        """
        endpoint = 'v2/tariffs/calculate'
        body = {
            "parameters": {"campaignId": self.campaignId},
            "offers": [
                {
                    "categoryId": offer["categoryId"],
                    "price": offer["price"],
                    "quantity": offer.get("quantity", 1),
                    "length": offer.get("length", 1),
                    "width": offer.get("width", 1),
                    "height": offer.get("height", 1),
                    "weight": offer.get("weight", 1),
                }
                for offer in offers
            ]
        }
        return await self._request('POST', endpoint, CalculateTariffsResponse, json=body, extra_headers=headers)
