import {
    Board
} from './types.js';

import fetch, {
    RequestInit
} from 'node-fetch';

export class HttpError extends Error {}

class Api {
    protected async get<T>(path: string, params: ConstructorParameters<typeof URLSearchParams>[0]): Promise<T> {
        const searchParams = new URLSearchParams(params);
        const requestInit: RequestInit = {
            method: 'GET',
        };

        const response = await fetch(`${this.baseUrl}/${path}?${searchParams.toString()}`, requestInit);
        if (!response.ok) {
            throw new HttpError(`HTTP error! status: ${response.status}`);
        }

        return response.json() as Promise<T>;
    }

    constructor(
        protected baseUrl: string
    ) {
    }
}

export class BitflyerApi extends Api {
    public async getBoard(): Promise<Board> {
        const path = "getboard";
        const params = {
            product_code: this.cryptoCurrencyCode,
        };

        return this.get<Board>(path, params);
    }

    constructor(
        baseUrl: string,
        protected cryptoCurrencyCode: string
    ) {
        super(baseUrl);
    }
}