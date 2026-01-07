import requests

from ._types import Board


class ApiClient:
    _base_url: str
    
    def get_board(self) -> Board:
        path = "getboard"
        params = {
            "product_code": self._crypto_currency_code
        }
        
        response = requests.get(self._base_url + path, params=params)
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
        
        return response.json()
    
    def __init__(self,
                 base_url: str,
                 crypto_currency_code: str):
        self._base_url = base_url
        self._crypto_currency_code = crypto_currency_code