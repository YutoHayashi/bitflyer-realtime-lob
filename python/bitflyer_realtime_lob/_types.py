from typing import TypedDict, List


class LimitOrder(TypedDict):
    price: float
    size: float


class Board(TypedDict):
    bids: List[LimitOrder]
    asks: List[LimitOrder]
    mid_price: float
    spread: float