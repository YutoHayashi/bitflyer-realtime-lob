from typing import Self

import threading

from dependency_injector import containers, providers
from dotenv import dotenv_values

from .logger import Logger
from .api_client import ApiClient
from .data_store import DataStore
from .stream import Stream
from .message_handler import (
    LightningBoardOpenMessageHandler,
    LightningBoardMessageHandler
)


class App(containers.DeclarativeContainer):
    config = providers.Configuration(default={
        "api_base_url": dotenv_values().get("BITFLYER_API_BASE_URL"),
        "rpc_url": dotenv_values().get("BITFLYER_RPC_URL"),
        "crypto_currency_code": dotenv_values().get("BITFLYER_CRYPTO_CURRENCY_CODE"),
        "log_output_directory": dotenv_values().get("LOG_OUTPUT_DIRECTORY"),
    })
    
    logger = providers.Singleton(Logger,
        output_directory=config.log_output_directory)
    
    api_client = providers.Singleton(ApiClient,
        base_url=config.api_base_url,
        crypto_currency_code=config.crypto_currency_code)
    
    data_store = providers.Singleton(DataStore)
    
    stream = providers.Singleton(Stream,
        rpc_url=config.rpc_url,
        crypto_currency_code=config.crypto_currency_code,
        message_handlers=providers.List(
            providers.Factory(LightningBoardOpenMessageHandler,
                crypto_currency_code=config.crypto_currency_code,
                api_client=api_client,
                data_store=data_store),
            providers.Factory(LightningBoardMessageHandler,
                crypto_currency_code=config.crypto_currency_code,
                data_store=data_store),
        ),
        logger=logger)
    
    @classmethod
    def to_threaded(cls) -> tuple[threading.Thread, Self]:
        import asyncio
        
        app = cls()
        
        thread = threading.Thread(
            target=lambda: asyncio.run(app.stream().run()),
            daemon=True)
        return thread, app


if __name__ == "__main__":
    import sys
    import os
    
    def print_board(book):
        os.system('cls' if os.name == 'nt' else 'clear')
        
        bids = book['bids']
        asks = book['asks']
        mid = book['mid_price']
        spread = book['spread']
        
        print(f"Realtime LOB\nSpread: {spread:.2f}" if mid and spread else "Realtime LOB | Waiting for data...")
        print("-" * 30)
        print(f"{'Size':>10} | {'Price':>10}")
        print("-" * 30)
        
        for ask in reversed(asks):
            print(f"\033[91m{ask['size']:>10.4f} | {ask['price']:>10.2f}\033[0m")
            
        print("-" * 30)
        
        print(f"{'':>10} | {mid:>10.2f}")
        
        print("-" * 30)
        
        for bid in bids:
            print(f"\033[92m{bid['size']:>10.4f} | {bid['price']:>10.2f}\033[0m")
            
        print("-" * 30)

    try:
        thread, app = App.to_threaded()
        
        app.data_store().on_update(lambda store: print_board(store.get_book(depth=25)))
        
        thread.start()
        while thread.is_alive():
            thread.join(1)
    except KeyboardInterrupt:
        sys.exit(1)