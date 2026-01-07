from abc import ABC, abstractmethod

from .api_client import ApiClient
from .data_store import DataStore


class MessageHandler(ABC):
    @property
    @abstractmethod
    def channel(self) -> str: ...
    
    @abstractmethod
    async def handle(self, data: list|dict) -> None: ...


class LightningBoardOpenMessageHandler(MessageHandler):
    channel: str = ""
    
    async def handle(self, data: list|dict) -> None:
        await self.data_store.init_market(**self.api_client.get_board())
    
    def __init__(self,
                 crypto_currency_code: str,
                 api_client: ApiClient,
                 data_store: DataStore):
        self.channel = f"subscribe_lightning_board_{crypto_currency_code}"
        self.api_client = api_client
        self.data_store = data_store


class LightningBoardMessageHandler(MessageHandler):
    channel: str = ""
    
    async def handle(self, data: list|dict) -> None:
        await self.data_store.update_market(
            bids=data.get("bids", []),
            asks=data.get("asks", []),
            mid_price=data.get("mid_price", None)
        )
    
    def __init__(self,
                 crypto_currency_code: str,
                 data_store: DataStore):
        self.channel = f"lightning_board_{crypto_currency_code}"
        self.data_store = data_store