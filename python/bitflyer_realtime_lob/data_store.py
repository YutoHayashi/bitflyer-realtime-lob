from typing import Dict, List, Optional, Any, Callable
import asyncio
import math

from ._types import LimitOrder


class DataStore:
    def on_update(self, callback: Callable[['DataStore'], None]) -> None:
        self._callbacks.append(callback)
    
    def _notify_callbacks(self) -> None:
        for callback in self._callbacks:
            callback(self)
    
    def _update_metrics(self) -> None:
        best_bid_order = max(self.bids, key=lambda x: x.get("price")) if self.bids else None
        best_ask_order = min(self.asks, key=lambda x: x.get("price")) if self.asks else None
        
        if best_bid_order is not None and best_ask_order is not None:
            self.spread = best_ask_order["price"] - best_bid_order["price"]
        else:
            self.spread = None
    
    async def init_market(self, bids: List[LimitOrder], asks: List[LimitOrder], mid_price: float) -> None:
        self.bids = bids
        self.asks = asks
        self.mid_price = mid_price
        
        self._is_initialized = True
        
        async with self.lock:
            for update in self._update_buffer:
                await self.update_market(**update)
            self._update_buffer.clear()
        
        self._update_metrics()
        self._notify_callbacks()
    
    async def update_market(self, bids: List[LimitOrder] = [], asks: List[LimitOrder] = [], mid_price: Optional[float] = None) -> None:
        if not self._is_initialized:
            self._update_buffer.append({
                "bids": bids,
                "asks": asks,
                "mid_price": mid_price
            })
            return
        
        async with self.lock:
            if mid_price is not None:
                self.mid_price = mid_price
                
                asks_to_move = [o for o in self.asks if o["price"] < self.mid_price]
                self.asks = [o for o in self.asks if not o["price"] < self.mid_price]

                bids_to_move = [o for o in self.bids if o["price"] > self.mid_price]
                self.bids = [o for o in self.bids if not o["price"] > self.mid_price]

                self.bids.extend(asks_to_move)
                self.asks.extend(bids_to_move)

            def update_list(order_list: List[LimitOrder], order: LimitOrder):
                price = order["price"]
                size = order["size"]
                new_list = [o for o in order_list if not math.isclose(o["price"], price)]
                if not math.isclose(size, 0):
                    new_list.append(order)
                return new_list

            for order in bids:
                self.bids = update_list(self.bids, order)
            
            for order in asks:
                self.asks = update_list(self.asks, order)
        
        self._update_metrics()
        self._notify_callbacks()
    
    def get_book(self, depth: int) -> Dict[str, Any]:
        sorted_bids = sorted(self.bids, key=lambda x: x.get("price"), reverse=True)[:depth]
        sorted_asks = sorted(self.asks, key=lambda x: x.get("price"))[:depth]
        
        return {
            "bids": sorted_bids,
            "asks": sorted_asks,
            "mid_price": self.mid_price,
            "spread": self.spread
        }
    
    def __init__(self):
        self.bids: List[LimitOrder] = []
        self.asks: List[LimitOrder] = []
        self.mid_price: Optional[float] = None
        self.spread: Optional[float] = None
        self._callbacks: List[Callable[['DataStore'], None]] = []
        self._is_initialized: bool = False
        self._update_buffer: List[Dict[str, Any]] = []
        self.lock = asyncio.Lock()