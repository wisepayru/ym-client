from tenacity import (
    retry,
    wait_fixed,
    stop_after_attempt
)
import requests
from .models import OrderResponse

class Client:
    def __init__(
            self, 
            schema: str = 'https', 
            url: str = 'api.partner.market.yandex.ru',
            campaignId: int = None,
            token: str = None):
        if token == None:
            raise Exception("Yandex Market API token was not provided. In order to init a Y.Market client, please provide a token.")
        self.schema = schema
        self.url = url
        self.token = token
        self.campaignId = campaignId
        self.headers = {
            "User-Agent": "github:wisepay/ym-api",
            "Api-Key": token
        }


    def get_order(self, orderId: int):
        endpoint = f'v2/campaigns/{self.campaignId}/orders/{orderId}'
        headers = self.headers
        order_details = requests.get(
            url=f'{self.schema}://{self.url}/{endpoint}',
            headers=headers
        )
        order_obj = OrderResponse(**order_details.json())
        return order_obj
