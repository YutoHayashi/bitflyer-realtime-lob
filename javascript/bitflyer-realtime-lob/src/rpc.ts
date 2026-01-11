import {
    WebSocket,
    type Event,
    type ErrorEvent,
    type CloseEvent,
    type MessageEvent,
} from 'ws';

import {
    Board
} from './types.js';

export type JsonRpcRequest = {
    jsonrpc: '2.0';
    id: string;
    method: string;
    params: {
        channel: string;
    };
};

export type JsonRpcResponse = {
    jsonrpc: '2.0';
};

export type JsonRpcConnectedResponse = JsonRpcResponse & {
    result: boolean;
    id: string;
};

export type JsonRpcMessageResponse<T = any> = JsonRpcResponse & {
    method: 'channelMessage';
    params: {
        channel: string;
        message: T;
    };
};

export interface JsonRpcMessageHandler<T = any> {
    idOrChannel: string;
    handleMessage(message: T): Promise<void>;
}

export abstract class AbstractJsonRpcMessageHandler<T = any> implements JsonRpcMessageHandler<T> {
    abstract idOrChannel: string;
    abstract handleMessage(message: T): Promise<void>;
}

export class BitflyerJsonRpc extends WebSocket {
    protected handleMessage(idOrChannel: string, message: any) {
        for (const handler of this.messageHandlers) {
            if (handler.idOrChannel === idOrChannel) {
                handler.handleMessage(message);
            }
        }
    }

    protected sendPublicSubscriptions() {
        for (const channel of this.publicChannels) {
            const request: JsonRpcRequest = {
                jsonrpc: '2.0',
                id: `subscribe_${channel}`,
                method: 'subscribe',
                params: {
                    channel
                },
            };
            this.send(JSON.stringify(request));
        }
    }

    public run() {
        this.onopen = this._onopen.bind(this);
        this.onclose = this._onclose.bind(this);
        this.onerror = this._onerror.bind(this);
        this.onmessage = this._onmessage.bind(this);
    }

    protected _onopen = (event: Event) => {
        console.log('WebSocket connection opened:', event);
        this.sendPublicSubscriptions();
    }

    protected _onclose = (event: CloseEvent) => {
        console.log('WebSocket connection closed:', event);
    }

    protected _onerror = (event: ErrorEvent) => {
        console.error('WebSocket error occurred:', event);
    }

    protected _onmessage = (event: MessageEvent) => {
        const message = JSON.parse(event.data.toString()) as JsonRpcMessageResponse<Partial<Board>> | JsonRpcConnectedResponse;

        if ("method" in message && message.method === 'channelMessage') {
            this.handleMessage(message.params.channel, message.params.message);
            return;
        }

        if ("id" in message && "result" in message && message.result === true) {
            console.log(`Subscription to ${message.id} successful.`);
            this.handleMessage(message.id, message);
            return;
        }
    }

    constructor(
        rpcUrl: string,
        protected publicChannels: string[],
        protected messageHandlers: JsonRpcMessageHandler[]
    ) {
        super(rpcUrl);
    }
}