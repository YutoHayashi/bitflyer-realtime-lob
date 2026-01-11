export type LimitOrder = {
    price: number;
    size: number;
};

export type Board = {
    bids: LimitOrder[];
    asks: LimitOrder[];
    mid_price: number;
};