import httpx
from typing import Tuple, List, Dict, Any, Union
from uuid import UUID
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from .models import OrderResponse
from .models.generic import GenericSuccessResponse, GenericErrorResponse

class Client:
    def __init__(
            self, 
            schema: str = 'https', 
            url: str = 'api.partner.market.yandex.ru',
            campaignId: int = None,
            token: str = None):
        if token is None:
            raise Exception("Yandex Market API token was not provided. In order to init a Y.Market client, please provide a token.")
        if campaignId is None:
            raise Exception("Yandex Market campaignId was not provided.")
            
        self.base_url = f'{schema}://{url}'
        self.campaignId = campaignId
        self._token = token
        self._headers = {
            "User-Agent": "github:wisepay/ym-api",
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
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def _request(self, method: str, url: str, **kwargs) -> Tuple[httpx.Request, httpx.Response, dict]:
        """
        Helper method to make a request and handle responses.
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with Client(...)'.")
        
        req = self._client.build_request(method, url, **kwargs)
        resp = await self._client.send(req)
        
        resp.raise_for_status() # Raise an exception for 4xx or 5xx status codes
        
        return req, resp, resp.json()

    async def getOrder(self, orderId: int) -> Tuple[httpx.Request, httpx.Response, Union[OrderResponse, GenericErrorResponse]]:
        """
        Retrieve an order by its ID.
        https://yandex.ru/dev/market/partner-api/doc/ru/reference/orders/getOrder
        """
        endpoint = f'v2/campaigns/{self.campaignId}/orders/{orderId}'
        req, resp, data = await self._request('GET', endpoint)
        
        if 'errors' in data:
            return req, resp, GenericErrorResponse.model_validate(data)

        order_obj = OrderResponse.model_validate(data)
        return req, resp, order_obj

    async def deliverDigitalGoods(self, orderId: int, items: list) -> Tuple[httpx.Request, httpx.Response, Union[GenericSuccessResponse, GenericErrorResponse]]:
        """
        Provide digital codes for an order.
        https://yandex.ru/dev/market/partner-api/doc/ru/reference/orders/provideOrderDigitalCodes
        """
        endpoint = f'v2/campaigns/{self.campaignId}/orders/{orderId}/deliverDigitalGoods'
        body = {"items": items}

        req, resp, data = await self._request('POST', endpoint, json=body)

        if 'errors' in data:
            return req, resp, GenericErrorResponse.model_validate(data)
        
        return req, resp, GenericSuccessResponse.model_validate(data)

    async def setOrderExternalId(self, orderId: int, externalOrderId: UUID) -> Tuple[httpx.Request, httpx.Response, Union[GenericSuccessResponse, GenericErrorResponse]]:
        """
        Sets an external identifier for an order.
        https://yandex.ru/dev/market/partner-api/doc/ru/reference/orders/updateExternalOrderId
        """
        endpoint = f'v2/campaigns/{self.campaignId}/orders/{orderId}/external-id'
        body = {"externalOrderId": str(externalOrderId)}

        req, resp, data = await self._request('POST', endpoint, json=body)

        if 'errors' in data:
            return req, resp, GenericErrorResponse.model_validate(data)

        return req, resp, GenericSuccessResponse.model_validate(data)

