import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from .models import OrderResponse

class Client:
    def __init__(
            self, 
            schema: str = 'https', 
            url: str = 'api.partner.market.yandex.ru',
            campaignId: int = None,
            token: str = None):
        if token is None:
            raise Exception("Yandex Market API token was not provided. In order to init a Y.Market client, please provide a token.")
        self.schema = schema
        self.url = url
        self.token = token
        self.campaignId = campaignId
        self.base_url = f'{self.schema}://{self.url}'
        self.headers = {
            "User-Agent": "github:wisepay/ym-api",
            "Api-Key": token
        }
        self._client = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(headers=self.headers, timeout=10.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(httpx.RequestError)
    )
    async def getOrder(self, orderId: int):
        # https://yandex.ru/dev/market/partner-api/doc/ru/reference/orders/getOrder
        endpoint = f'v2/campaigns/{self.campaignId}/orders/{orderId}'
        url = f'{self.base_url}/{endpoint}'
        
        req = self._client.build_request('GET', url)
        resp = await self._client.send(req)
        
        resp.raise_for_status()
        
        order_obj = OrderResponse(**resp.json())
        return req, resp, order_obj

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(httpx.RequestError)
    )
    async def deliverDigitalGoods(self, orderId: int, items: list):
        # https://yandex.ru/dev/market/partner-api/doc/ru/reference/orders/provideOrderDigitalCodes
        endpoint = f'v2/campaigns/{self.campaignId}/orders/{orderId}/deliverDigitalGoods'
        url = f'{self.base_url}/{endpoint}'
        body = {
            "items": items
        }

        req = self._client.build_request('POST', url, json=body)
        resp = await self._client.send(req)

        resp.raise_for_status()
        return req, resp, resp.json()
