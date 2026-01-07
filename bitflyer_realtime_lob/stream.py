from typing import List, Optional
import asyncio
import json

from websockets import ClientConnection
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
from websockets.asyncio.client import connect

from .logger import Logger
from .message_handler import MessageHandler


class Stream:
    _rpc_url: str
    
    async def _handle_message(self, channel: str, message: Optional[dict|list]) -> None:
        tasks = []
        
        for message_handler in self._message_handlers:
            if isinstance(message_handler, MessageHandler):
                if message_handler.channel == channel:
                    tasks.append(message_handler.handle(message or []))
        
        if tasks: await asyncio.gather(*tasks)
    
    async def _send_public_subscriptions(self, websocket: ClientConnection) -> None:
        for channel in self._public_channels:
            message = json.dumps({
                "id": f"subscribe_{channel}",
                "method": "subscribe",
                "params": {
                    "channel": channel,
                }
            })
            
            await websocket.send(message.encode(), text=True)
    
    async def _receive_messages(self, websocket: ClientConnection) -> None:
        while True:
            message = await websocket.recv()
            message = json.loads(message)
            
            if "params" in message and "message" in message["params"] and "channel" in message["params"]:
                await self._handle_message(message["params"]["channel"], message["params"]["message"])
                continue
            
            if "id" in message and "result" in message and message["result"] is True:
                self._logger.info(f"Subscription successful for id: {message['id']}")
                await self._handle_message(message["id"], message)
                continue
            
            if "error" in message:
                self._logger.error(f"Error message received (code: {message['error']['code']}): {message['error']['message']}")
    
    async def run(self) -> None:
        async for websocket in connect(self._rpc_url):
            try:
                await asyncio.gather(
                    self._send_public_subscriptions(websocket),
                    self._receive_messages(websocket)
                )
            except ConnectionClosedOK as e:
                self._logger.warning(f"Connection closed: {e}, reconnecting.")
            except ConnectionClosedError as e:
                self._logger.error(f"Connection closed with error: {e}, reconnecting.")
            except Exception as e:
                self._logger.error(f"Unexpected error: {e}, reconnecting.")
    
    def __init__(self,
                 rpc_url: str,
                 crypto_currency_code: str,
                 message_handlers: List[MessageHandler],
                 logger: Logger):
        self._rpc_url = rpc_url
        self._crypto_currency_code = crypto_currency_code
        self._message_handlers = message_handlers
        self._logger = logger
        
        self._public_channels = [
            f"lightning_board_{crypto_currency_code}",
        ]