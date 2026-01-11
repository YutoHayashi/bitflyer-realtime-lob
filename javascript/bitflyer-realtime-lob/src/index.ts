import {
    Container,
} from 'inversify';

import {
    AbstractJsonRpcMessageHandler,
    BitflyerJsonRpc
} from './rpc.js';
import { BitflyerApi } from './http.js';
import { Store } from './data.js';
import { Board } from './types.js';

class LightningBoardOpenHandler extends AbstractJsonRpcMessageHandler<boolean> {
    public async handleMessage(): Promise<void> {
        const board = await this.bitflyerApi.getBoard();
        await this.store.initBoard(board);
    }

    constructor(
        public idOrChannel: string,
        protected bitflyerApi: BitflyerApi,
        protected store: Store
    ) {
        super();
    }
}

class LightningBoardHandler extends AbstractJsonRpcMessageHandler<Partial<Board>> {
    public async handleMessage(message: Partial<Board>): Promise<void> {
        this.store.updateBoard(message);
    }

    constructor(
        public idOrChannel: string,
        protected store: Store
    ) {
        super();
    }
}

export default class extends Container {
    constructor(
        cryptoCurrencyCode: string,
    ) {
        super();

        this.bind<Store>('store').to(Store).inSingletonScope();
        this.bind<BitflyerApi>('bitflyerApi').toDynamicValue(() => {
            return new BitflyerApi(
                "https://api.bitflyer.com/v1",
                cryptoCurrencyCode
            );
        });
        this.bind<LightningBoardOpenHandler>('lightningBoardOpenHandler').toDynamicValue(context => {
            return new LightningBoardOpenHandler(
                `subscribe_lightning_board_${cryptoCurrencyCode}`,
                context.get<BitflyerApi>('bitflyerApi'),
                context.get<Store>('store')
            );
        });
        this.bind<LightningBoardHandler>('lightningBoardHandler').toDynamicValue(context => {
            return new LightningBoardHandler(
                `lightning_board_${cryptoCurrencyCode}`,
                context.get<Store>('store')
            );
        });
        this.bind<BitflyerJsonRpc>('bitflyerJsonRpc').toDynamicValue(context => {
            return new BitflyerJsonRpc(
                "wss://ws.lightstream.bitflyer.com/json-rpc",
                [`lightning_board_${cryptoCurrencyCode}`],
                [
                    context.get<LightningBoardOpenHandler>('lightningBoardOpenHandler'),
                    context.get<LightningBoardHandler>('lightningBoardHandler')
                ]
            );
        });
    }
}