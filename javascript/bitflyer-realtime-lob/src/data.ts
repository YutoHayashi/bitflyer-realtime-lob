import {
    LimitOrder,
    Board
} from './types.js';

export type UpdateCallback = (store: Store) => void;

export class Store {
    protected bids: LimitOrder[];
    protected asks: LimitOrder[];
    protected midPrice: number | null;
    protected spread: number | null;

    protected updateCallbacks: UpdateCallback[];
    protected isInitialized: boolean;
    protected updateBuffer: Partial<Board>[];

    public onUpdate(callback: UpdateCallback): void {
        this.updateCallbacks.push(callback);
    }

    protected notifyCallbacks(): void {
        for (const callback of this.updateCallbacks) {
            callback(this);
        }
    }

    protected updateMetrics(): void {
        if (this.asks.length === 0 || this.bids.length === 0) {
            this.spread = null;
            return;
        }

        const bestBid = this.bids.sort((a, b) => b.price - a.price)[0] as LimitOrder;
        const bestAsk = this.asks.sort((a, b) => a.price - b.price)[0] as LimitOrder;

        this.spread = bestAsk.price - bestBid.price;
    }

    public updateBoard(update: Partial<Board>): void {
        if (!this.isInitialized) {
            this.updateBuffer.push(update);
            return;
        }

        const asks = update?.asks || [];
        const bids = update?.bids || [];
        const midPrice = update?.mid_price || null;

        if (midPrice !== null) {
            this.midPrice = midPrice;

            const asks_to_move = this.asks.filter(ask => ask.price < midPrice);
            const bids_to_move = this.bids.filter(bid => bid.price > midPrice);

            this.asks = this.asks.filter(ask => ask.price >= midPrice);
            this.asks.push(...bids_to_move);

            this.bids = this.bids.filter(bid => bid.price <= midPrice);
            this.bids.push(...asks_to_move);
        }

        for (const ask of asks) {
            const price = ask.price;
            const size = ask.size;

            this.asks = this.asks.filter(a => a.price !== price);
            if (size > 0) {
                this.asks.push(ask);
            }
        }

        for (const bid of bids) {
            const price = bid.price;
            const size = bid.size;

            this.bids = this.bids.filter(b => b.price !== price);
            if (size > 0) {
                this.bids.push(bid);
            }
        }

        this.updateMetrics();
        this.notifyCallbacks();
    }

    public initBoard(board: Board): void {
        this.bids = board.bids;
        this.asks = board.asks;
        this.midPrice = board.mid_price;

        this.isInitialized = true;

        for (const buffer of this.updateBuffer) {
            this.updateBoard(buffer);
        }

        this.updateBuffer = [];

        this.updateMetrics();
        this.notifyCallbacks();
    }

    public getBoard(): Pick<Board, 'bids' | 'asks'> & { mid_price: number | null, spread: number | null } {
        return {
            bids: this.bids.sort((a, b) => b.price - a.price),
            asks: this.asks.sort((a, b) => a.price - b.price),
            mid_price: this.midPrice,
            spread: this.spread,
        }
    }

    constructor() {
        this.bids = [];
        this.asks = [];
        this.midPrice = null;
        this.spread = null;
        this.isInitialized = false;
        this.updateBuffer = [];
        this.updateCallbacks = [];
    }
}