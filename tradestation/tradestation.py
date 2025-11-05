
import json
from typing import AsyncGenerator
import os
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional, Union, List, Generator, AsyncGenerator, Tuple
import json
import httpx
import asyncio
from aiohttp import web
import threading
import re
from models import *

AUTH_URL = "https://signin.tradestation.com/authorize"
TOKEN_URL = "https://signin.tradestation.com/oauth/token"
LIVE_API_URL = "https://api.tradestation.com"
DEMO_API_URL = "https://sim-api.tradestation.com"
auth_success_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authentication Successful</title>
    <script>
        setTimeout(() => {
            window.close();
        }, 1000);
    </script>
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: Arial, sans-serif;
            font-size: 24px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    Authentication successful!
</body>
</html>
"""

class OAuthHandler(BaseHTTPRequestHandler):
    """Handles OAuth authentication callback from TradeStation."""
    access_token = None
    
    def do_GET(self):
        print("Received GET request")
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        if 'code' not in query_params:
            self.send_error(400, "Error: No code received")
            return

        self.send_response(200)
        self.end_headers()
        # with open("auth_success.html", 'rb') as f:
        #     self.wfile.write(f.read())
        self.wfile.write(auth_success_html.encode('utf-8'))
        # Exchange code for token
        code = query_params['code'][0]
        self.server.auth_instance._exchange_code_for_token(code)

        # Stop the server
        threading.Thread(target=self.server.shutdown).start()

class TradeStationClient:
    """Client for interacting with the TradeStation API."""
    ### Initiation and Authentication handling ###
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, port: int = 31022,
                 is_demo: bool = True, refresh_token_margin:float=60, async_mode: bool = False):
        self.client_id = client_id if client_id else os.getenv('TRADESTATION_CLIENT_ID')
        self.client_secret = client_secret if client_secret else os.getenv('TRADESTATION_CLIENT_SECRET')
        assert self.client_id, "Either client_id or CLIENT_ID environment variable must be provided."
        assert self.client_secret, "Either client_secret or CLIENT_SECRET environment variable must be provided."
        self.port=port
        self.base_url = DEMO_API_URL if is_demo else LIVE_API_URL
        self.redirect_uri = f'http://localhost:{self.port}/'
        self.access_token = None
        self.refresh_token = None
        self.expires_in = None
        self.refresh_margin = timedelta(seconds=refresh_token_margin)
        self._authenticate()
        self.client = httpx.AsyncClient(headers={'Authorization': f'Bearer {self.access_token}'})


    def _generate_auth_url(self) -> str:
        """Generates the authentication URL for TradeStation OAuth."""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'audience': 'https://api.tradestation.com',
            'redirect_uri': self.redirect_uri,
            'scope': 'openid profile offline_access MarketData ReadAccount Trade',
            'state': 'xyzv'  # Use a secure state to prevent CSRF attacks
        }
        return f"https://signin.tradestation.com/authorize?{urlencode(params)}"
    
    def _start_server(self):
        """Starts a local HTTP server to handle OAuth callback."""
        OAuthHandler.access_token = None
        server = HTTPServer(("127.0.0.1", self.port), OAuthHandler)
        server.auth_instance = self
        threading.Thread(target=server.serve_forever, daemon=True).start()

    def _authenticate(self):
        """Handles the authentication flow."""
        self._start_server()
        webbrowser.open(self._generate_auth_url())
        # print(self._generate_auth_url())
        
        while self.access_token is None:
            pass

    def _exchange_code_for_token(self, code: str):
        """Exchanges authorization code for an access token."""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        with httpx.Client() as client:
            response = client.post(TOKEN_URL, data=data, headers=headers)
            if response.status_code == 200:
                body = response.json()
                self.access_token = body['access_token']
                self.refresh_token = body['refresh_token']
                self.token_expiry = datetime.now() + timedelta(seconds=body.get('expires_in', 1200))
            else:
                raise ValueError(f"Error obtaining token: {response.text}")


    async def suggestsymbols(self, text: str, dollar_top: Optional[int] = None, dollar_filter: Optional[str] = None) -> Union[Error, SymbolSuggestDefinition]:
        """Suggest Symbols\n

Args:
    dollar_top: The top number of results to return.
    dollar_filter: An OData filter to apply to the results. Supports the `eq` and `neq` filter opeators. E.g. `AAP?$filter=Category%20neq%20%27Stock%27`.\nValid values are: `Category` (`Stock`, `Index`, `Future`, `Forex`), `Country` (E.g. `United States`, `GB`) `Currency` (E.g. `USD`, `AUD`),\nand `Exchange` (E.g. `NYSE`).
    text: Symbol text for suggestion. Partial input of a symbol name, company name, or description."""
        url = f"{self.base_url}/v2/data/symbols/suggest/{text}"
        response = await self.client.get(url, params={k: v for k, v in {'$top': dollar_top, '$filter': dollar_filter}.items() if v is not None})
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 500, 502, 504}:
            if response.status_code == 200: return SymbolSuggestDefinition.from_dict(response.json())
            if response.status_code == 400: return Error.from_dict(response.json())
            if response.status_code == 401: return Error.from_dict(response.json())
            if response.status_code == 403: return Error.from_dict(response.json())
            if response.status_code == 500: return Error.from_dict(response.json())
            if response.status_code == 502: return Error.from_dict(response.json())
            if response.status_code == 504: return Error.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def search_symbols(self, criteria: str) -> Union[Error, SymbolSearchDefinition]:
        """
        Search for Symbols

        Args:
            criteria: Criteria are represented as Key/value pairs (`&` separated):
                `N`: Name of Symbol. (Optional)
                `C`: Asset categories. (Optional) Possible values:
                        - `Future` or `FU`
                        - `FutureOption` or `FO`
                        - `Stock` or `S` (Default)
                        - `StockOption` or `SO` (If root is specified, default category)
                        - `Index` or `IDX`
                        - `CurrencyOption` or `CO`
                        - `MutualFund` or `MF`
                        - `MoneyMarketFund` or `MMF`
                        - `IndexOption` or `IO`
                        - `Bond` or `B`
                        - `Forex` or `FX`

                `Cnt`: Country where the symbol is traded in. (Optional) Possible values:
                        - `ALL` if not specified (Default)
                        - `US`
                        - `DE`
                        - `CA`
            #### For Equities Lookups:
                 
                `N`: partial/full symbol name, will return all symbols that contain the provided name value
                
                `Desc`: Name of the company
                
                `Flg`: indicates whether symbols no longer trading should be included in the results returned. (Optional) This criteria is not returned in the symbol data. Possible values:
                    - `true`
                    - `false` (Default)
                    
                `Cnt`: Country where the symbol is traded in. (Optional) Possible values:\n  - `ALL` if not specified (Default)\n  - `US`\n  - `DE`\n  - `CA`\n\n#### For Options Lookups:\n(Category=StockOption, IndexOption, FutureOption or CurrencyOption)\n\n`R`: Symbol root. Required field, the symbol the option is a derivative of, this search will not return options based on a partial root.\n\n`Stk`: Number of strikes prices above and below the underlying price\n  - Default value 3\n\n`Spl`: Strike price low\n\n`Sph`: Strike price high\n\n`Exd`: Number of expiration dates.\n  - Default value 3\n\n`Edl`: Expiration date low, ex: 01-05-2011\n\n`Edh`: Expiration date high, ex: 01-20-2011\n\n`OT`: Option type. Possible values:\n  - `Both` (Default)\n  - `Call`\n  - `Put`\n\n`FT`: Future type for FutureOptions. Possible values:\n  - `Electronic` (Default)\n  - `Pit`\n\n`ST`: Symbol type: Possible values:\n  - `Both`\n  - `Composite` (Default)\n  - `Regional`\n\n#### For Futures Lookups:\n(Category = Future)\n\n`Desc`: Description of symbol traded\n\n`R`: Symbol root future trades\n\n`FT`: Futures type. Possible values:\n  - `None`\n  - `PIT`\n  - `Electronic` (Default)\n  - `Combined`\n\n`Cur`: Currency. Possible values:\n  - `All`\n  - `USD` (Default)\n  - `AUD`\n  - `CAD`\n  - `CHF`\n  - `DKK`\n  - `EUR`\n  - `DBP`\n  - `HKD`\n  - `JPY`\n  - `NOK`\n  - `NZD`\n  - `SEK`\n  - `SGD`\n\n`Exp`: whether to include expired contracts\n  - `false` (Default)\n  - `true`\n\n`Cnt`: Country where the symbol is traded in. (Optional) Possible values:\n  - `ALL` if not specified (Default)\n  - `US`\n  - `DE`\n  - `CA`\n\n#### For Forex Lookups:\n\n`N`: partial/full symbol name. Use all or null for a list of all forex symbols\n\n`Desc`: Description\n\nNote:\n  - The exchange returned for all forex searches will be `FX`\n  - The country returned for all forex searches will be `FOREX`\n"""
        url = f"{self.base_url}/v2/data/symbols/search/{criteria}"
        response = await self.client.get(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 500, 502, 504}:
            if response.status_code == 200: return SymbolSearchDefinition.from_dict(response.json())
            if response.status_code == 400: return Error.from_dict(response.json())
            if response.status_code == 401: return Error.from_dict(response.json())
            if response.status_code == 403: return Error.from_dict(response.json())
            if response.status_code == 404: return Error.from_dict(response.json())
            if response.status_code == 500: return Error.from_dict(response.json())
            if response.status_code == 502: return Error.from_dict(response.json())
            if response.status_code == 504: return Error.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def stream_tick_bars(self, symbol: str, interval: int, bars_back: int) -> Union[Error, TickbarDefinition]:
        """
        Stream Tick Bars

        Args:
            symbol: A Symbol Name
            interval: Interval for each bar returned (in ticks).
            bars_back: The number of bars to stream, going back from current time.
        """
        url = f"{self.base_url}/v2/stream/tickbars/{symbol}/{interval}/{bars_back}"
        response = await self.client.get(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 500, 502, 504}:
            if response.status_code == 200: return TickbarDefinition.from_dict(response.json())
            if response.status_code == 400: return Error.from_dict(response.json())
            if response.status_code == 401: return Error.from_dict(response.json())
            if response.status_code == 403: return Error.from_dict(response.json())
            if response.status_code == 404: return Error.from_dict(response.json())
            if response.status_code == 500: return Error.from_dict(response.json())
            if response.status_code == 502: return Error.from_dict(response.json())
            if response.status_code == 504: return Error.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_accounts(self, ) -> Union[Accounts, ErrorResponse]:
        """Get Accounts
"""
        url = f"{self.base_url}/v3/brokerage/accounts"
        response = await self.client.get(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return Accounts.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_balances(self, accounts: str) -> Union[Balances, ErrorResponse]:
        """Get Balances

Args:
    accounts: List of valid Account IDs for the authenticated user in comma separated format; for example `\"61999124,68910124\"`. 1 to 25 Account IDs can be specified, comma separated. Recommended batch size is 10."""
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/balances"
        response = await self.client.get(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return Balances.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_balances_bod(self, accounts: str) -> Union[BalancesBOD, ErrorResponse]:
        """Get Balances BOD

Args:
    accounts: List of valid Account IDs for the authenticated user in comma separated format; for example `\"61999124,68910124\"`. 1 to 25 Account IDs can be specified, comma separated. Recommended batch size is 10."""
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/bodbalances"
        response = await self.client.get(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return BalancesBOD.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_historical_orders(self, accounts: str, since: str, page_size: Optional[int] = 600, next_token: Optional[str] = None) -> Union[ErrorResponse, HistoricalOrders]:
        """Get Historical Orders

Args:
    accounts: List of valid Account IDs for the authenticated user in comma separated format; for example `\"61999124,68910124\"`. 1 to 25 Account IDs can be specified, comma separated. Recommended batch size is 10.
    since: Historical orders since date. For example `\"2006-01-13\",\"01-13-2006\",\"2006/01/13\",\"01/13/2006\"`. Limited to 90 days prior to the current date.
    page_size: The number of requests returned per page when paginating responses. If not provided, results will not be paginated and a maximum of 600 orders is returned.
    next_token: An encrypted token with a lifetime of 1 hour for use with paginated order responses. This is returned with paginated results, and used in only the subsequent request which will return a new nextToken until there are fewer returned orders than the requested pageSize. If the number of returned orders equals the pageSize, and there are no additional orders, the nextToken will not be generated."""
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/historicalorders"
        response = await self.client.get(url, params={k: v for k, v in {'since': since, 'pageSize': page_size, 'nextToken': next_token}.items() if v is not None})
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return HistoricalOrders.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_historical_orders_by_order_id(self, accounts: str, order_ids: str, since: str) -> Union[ErrorResponse, HistoricalOrdersById]:
        """Get Historical Orders By Order ID

Args:
    accounts: List of valid Account IDs for the authenticated user in comma separated format; for example `\"61999124,68910124\"`. 1 to 25 Account IDs can be specified, comma separated. Recommended batch size is 10.
    order_ids: List of valid Order IDs for the authenticated user for given accounts in comma separated format; for example `\"123456789,286179863\"`. 1 to 50 Order IDs can be specified, comma separated.
    since: Historical orders since date. For example `\"2006-01-13\",\"01-13-2006\",\"2006/01/13\",\"01/13/2006\"`. Limited to 90 days prior to the current date."""
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/historicalorders/{order_ids}"
        response = await self.client.get(url, params={k: v for k, v in {'since': since}.items() if v is not None})
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return HistoricalOrdersById.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_orders(self, accounts: str, page_size: Optional[int] = 600, next_token: Optional[str] = None) -> Union[ErrorResponse, Orders]:
        """Get Orders

Args:
    accounts: List of valid Account IDs for the authenticated user in comma separated format; for example `\"61999124,68910124\"`. 1 to 25 Account IDs can be specified, comma separated. Recommended batch size is 10.
    page_size: The number of requests returned per page when paginating responses. If not provided, results will not be paginated and a maximum of 600 orders is returned.
    next_token: An encrypted token with a lifetime of 1 hour for use with paginated order responses. This is returned with paginated results, and used in only the subsequent request which will return a new nextToken until there are fewer returned orders than the requested pageSize. If the number of returned orders equals the pageSize, and there are no additional orders, the nextToken will not be generated."""
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/orders"
        response = await self.client.get(url, params={k: v for k, v in {'pageSize': page_size, 'nextToken': next_token}.items() if v is not None})
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return Orders.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_orders_by_order_id(self, accounts: str, order_ids: str) -> Union[ErrorResponse, OrdersById]:
        """Get Orders By Order ID

Args:
    accounts: List of valid Account IDs for the authenticated user in comma separated format; for example `\"61999124,68910124\"`. 1 to 25 Account IDs can be specified, comma separated. Recommended batch size is 10.
    order_ids: List of valid Order IDs for the authenticated user for given accounts in comma separated format; for example `\"123456789,286179863\"`. 1 to 50 Order IDs can be specified, comma separated."""
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/orders/{order_ids}"
        response = await self.client.get(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return OrdersById.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_positions(self, accounts: str, symbol: Optional[str] = None) -> Union[ErrorResponse, Positions]:
        """Get Positions

Args:
    accounts: List of valid Account IDs for the authenticated user in comma separated format; for example `\"61999124,68910124\"`. 1 to 25 Account IDs can be specified, comma separated. Recommended batch size is 10.
    symbol: List of valid symbols in comma separated format; for example `MSFT,MSFT *,AAPL`. You can use an * as wildcard to make more complex filters.\n\nExamples of the wildcard being used: \n\n  * Get all options for MSFT: symbol=`MSFT *`\n  * Get MSFT and all its options: symbol=`MSFT,MSFT *`\n  * Get all MSFT options expiring in 2023: symbol=`MSFT 23*`\n  * Get all MSFT options expiring in March 2023: symbol=`MSFT 2303*`\n  * Get all options expiring in March 2023: symbol=`* 2303*`\n  * Get all call options expiring in March 2023: symbol=`* 2303*C*`\n  * Get BHM*: symbol=`BHM**`"""
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/positions"
        response = await self.client.get(url, params={k: v for k, v in {'symbol': symbol}.items() if v is not None})
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return Positions.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def confirm_order(self, body: OrderRequest) -> Union[ErrorResponse, List[OrderConfirmResponses]]:
        """Confirm Order
"""
        url = f"{self.base_url}/v3/orderexecution/orderconfirm"
        response = await self.client.post(url, json=body)
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return [OrderConfirmResponses.from_dict(i) for i in response.json()]
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def confirm_group_order(self, body: GroupOrderRequest) -> Union[ErrorResponse, List[OrderConfirmResponses]]:
        """Confirm Group Order
"""
        url = f"{self.base_url}/v3/orderexecution/ordergroupconfirm"
        response = await self.client.post(url, json=body)
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return [OrderConfirmResponses.from_dict(i) for i in response.json()]
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def place_group_order(self, body: GroupOrderRequest) -> Union[ErrorResponse, List[OrderResponses]]:
        """Place Group Order
"""
        url = f"{self.base_url}/v3/orderexecution/ordergroups"
        response = await self.client.post(url, json=body)
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return [OrderResponses.from_dict(i) for i in response.json()]
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def place_order(self, body: OrderRequest) -> Union[ErrorResponse, List[OrderResponses]]:
        """Place Order
"""
        url = f"{self.base_url}/v3/orderexecution/orders"
        print(json.dumps(body.to_dict(),indent=4))
        response = await self.client.post(url, json=body.to_dict(), headers={"content-type": "application/json","Authorization": f"Bearer {self.access_token}"})
        print(response.json())
        # response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return OrderResponses.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def replace_order(self, order_id: str, body: OrderReplaceRequest) -> Union[ErrorResponse, OrderResponse]:
        """Replace Order

Args:
    order_id: OrderID for order to replace. Equity, option or future orderIDs should not include dashes (E.g. `1-2345-6789`). Valid format orderId=`123456789`"""
        url = f"{self.base_url}/v3/orderexecution/orders/{order_id}"
        response = await self.client.put(url, json=body)
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return OrderResponse.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def cancel_order(self, order_id: str) -> Union[ErrorResponse, OrderResponse]:
        """Cancel Order

Args:
    order_id: Order ID for cancellation request. Equity, option or future orderIDs should not include dashes (E.g. `1-2345-6789`). Valid format orderId=`123456789`"""
        url = f"{self.base_url}/v3/orderexecution/orders/{order_id}"
        response = await self.client.delete(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return OrderResponse.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_bars(self, symbol: str, interval: Optional[str] = None, unit: Optional[str] = None, barsback: Optional[str] = None, firstdate: Optional[str] = None, lastdate: Optional[str] = None, sessiontemplate: Optional[str] = None, startdate: Optional[str] = None) -> Union[Bars, ErrorResponse]:
        """Get Bars

Args:
    symbol: The valid symbol string.
    interval: Default: `1`.  Interval that each bar will consist of -  for minute bars, the number of minutes aggregated in a single bar.  For bar units other than minute, value must be `1`.  For unit `Minute` the max allowed `Interval` is 1440.
    unit: Default: `Daily`. The unit of time for each bar interval. Valid values are: `Minute, Daily, Weekly, Monthly`.
    barsback: Default: `1`.  Number of bars back to fetch (or retrieve). The maximum number of intraday bars back that a user can query is 57,600. There is no limit on daily, weekly, or monthly bars. This parameter is mutually exclusive with `firstdate`
    firstdate: Does not have a default value. The first date formatted as `YYYY-MM-DD`,`2020-04-20T18:00:00Z`. This parameter is mutually exclusive with `barsback`.
    lastdate: Defaults to current timestamp. The last date formatted as `YYYY-MM-DD`,`2020-04-20T18:00:00Z`. This parameter is mutually exclusive with `startdate` and should be used instead of that parameter, since `startdate` is now deprecated.
    sessiontemplate: United States (US) stock market session templates, that extend bars returned to include \nthose outside of the regular trading session. Ignored for non-US equity symbols. Valid values are:\n`USEQPre`, `USEQPost`, `USEQPreAndPost`, `USEQ24Hour`,`Default`.
    startdate: Defaults to current timestamp. The last date formatted as `YYYY-MM-DD`,`2020-04-20T18:00:00Z`. This parameter is mutually exclusive with `lastdate`. This parameter is deprecated; use `lastdate` instead of `startdate`."""
        url = f"{self.base_url}/v3/marketdata/barcharts/{symbol}"
        response = await self.client.get(url, params={k: v for k, v in {'interval': interval, 'unit': unit, 'barsback': barsback, 'firstdate': firstdate, 'lastdate': lastdate, 'sessiontemplate': sessiontemplate, 'startdate': startdate}.items() if v is not None})
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return Bars.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def stream_bars(self, symbol: str, interval: Optional[str] = '1', unit: Optional[str] = 'Daily', barsback: Optional[str] = None, sessiontemplate: Optional[str] = None) -> AsyncGenerator[Union[Bar, Heartbeat, StreamErrorResponse], None]:
        """Stream Bars

Args:
    symbol: The valid symbol string.
Args:
    interval: Interval that each bar will consist of -  for minute bars, the number of\nminutes aggregated in a single bar. For bar units other than minute, value must be `1`.
Args:
    unit: Unit of time for each bar interval. Valid values are: `minute`, `daily`, `weekly`, and `monthly`.
Args:
    barsback: The bars back - the max value is 57600.
Args:
    sessiontemplate: United States (US) stock market session templates, that extend bars returned to include \nthose outside of the regular trading session. Ignored for non-US equity symbols. Valid values are:\n`USEQPre`, `USEQPost`, `USEQPreAndPost`, `USEQ24Hour`, `Default`."""
        url = f"{self.base_url}/v3/marketdata/stream/barcharts/{symbol}"
        async with self.client.stream('GET', url, params={k: v for k, v in {'interval': interval, 'unit': unit, 'barsback': barsback, 'sessiontemplate': sessiontemplate}.items() if v is not None}) as response:
            response.raise_for_status()
            print(response.status_code)
            if response.status_code in {400, 401, 403, 404, 429, 503, 504}:
                async for line in response.aiter_lines():
                    yield ErrorResponse.from_dict(json.loads(line))
            else:
                async for line in response.aiter_lines():
                    if not line or not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        # skip malformed lines
                        continue
                    yield TypeAdapter(Union[Bar, Heartbeat, StreamErrorResponse]).validate_python(obj)

    async def get_crypto_symbol_names(self, ) -> Union[ErrorResponse, SymbolNames]:
        """Get Crypto Symbol Names
"""
        url = f"{self.base_url}/v3/marketdata/symbollists/cryptopairs/symbolnames"
        response = await self.client.get(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return SymbolNames.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_symbol_details(self, symbols: str) -> Union[ErrorResponse, SymbolDetailsResponse]:
        """Get Symbol Details

Args:
    symbols: List of valid symbols in comma separated format; for example `\"MSFT,BTCUSD\"`, no more than 50 symbols per request."""
        url = f"{self.base_url}/v3/marketdata/symbols/{symbols}"
        response = await self.client.get(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return SymbolDetailsResponse.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_activation_triggers(self, ) -> Union[ActivationTriggers, ErrorResponse]:
        """Get Activation Triggers
"""
        url = f"{self.base_url}/v3/orderexecution/activationtriggers"
        response = await self.client.get(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return ActivationTriggers.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def routes(self, ) -> Union[ErrorResponse, Routes]:
        """Get Routes
"""
        url = f"{self.base_url}/v3/orderexecution/routes"
        response = await self.client.get(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return Routes.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_option_expirations(self, underlying: str, strike_price: Optional[float] = None) -> Union[ErrorResponse, Expirations]:
        """Get Option Expirations

Args:
    underlying: The symbol for the underlying security on which the option contracts are based. The underlying symbol must be an equity or index.
    strike_price: Strike price. If provided, only expirations for that strike price will be returned."""
        url = f"{self.base_url}/v3/marketdata/options/expirations/{underlying}"
        response = await self.client.get(url, params={k: v for k, v in {'strikePrice': strike_price}.items() if v is not None})
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 429, 503, 504}:
            if response.status_code == 200: return Expirations.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_option_risk_reward(self, body: RiskRewardAnalysisInput) -> Union[ErrorResponse, RiskRewardAnalysisResult]:
        """Get Option Risk Reward
"""
        url = f"{self.base_url}/v3/marketdata/options/riskreward"
        response = await self.client.post(url, json=body)
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 429, 503, 504}:
            if response.status_code == 200: return RiskRewardAnalysisResult.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_option_spread_types(self, ) -> Union[ErrorResponse, SpreadTypes]:
        """Get Option Spread Types
"""
        url = f"{self.base_url}/v3/marketdata/options/spreadtypes"
        response = await self.client.get(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 429, 503, 504}:
            if response.status_code == 200: return SpreadTypes.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_option_strikes(self, underlying: str, spread_type: Optional[str] = 'Single', strike_interval: Optional[int] = 1, expiration: Optional[str] = None, expiration2: Optional[str] = None) -> Union[ErrorResponse, Strikes]:
        """Get Option Strikes

Args:
    underlying: The symbol for the underlying security on which the option contracts are based. The underlying symbol must be an equity or index.
    spread_type: The name of the spread type to get the strikes for. This value can be obtained from the [Get Option Spread Types](#operation/GetOptionSpreadTypes) endpoint.
    strike_interval: Specifies the desired interval between the strike prices in a spread. It must be greater than or equal to 1. A value of 1 uses consecutive strikes; a value of 2 skips one between strikes; and so on.
    expiration: Date on which the option contract expires; must be a valid expiration date. Defaults to the next contract expiration date.
    expiration2: Second contract expiration date required for Calendar and Diagonal spreads."""
        url = f"{self.base_url}/v3/marketdata/options/strikes/{underlying}"
        response = await self.client.get(url, params={k: v for k, v in {'spreadType': spread_type, 'strikeInterval': strike_interval, 'expiration': expiration, 'expiration2': expiration2}.items() if v is not None})
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 429, 503, 504}:
            if response.status_code == 200: return Strikes.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_option_chain(self, underlying: str, expiration: Optional[str] = None, expiration2: Optional[str] = None, strike_proximity: Optional[int] = 5, spread_type: Optional[str] = 'Single', risk_free_rate: Optional[float] = None, price_center: Optional[float] = None, strike_interval: Optional[int] = 1, enable_greeks: Optional[bool] = True, strike_range: Optional[str] = 'All', option_type: Optional[str] = 'All') -> Union[ErrorResponse, Spread]:
        """Stream Option Chain

Args:
    underlying: The symbol for the underlying security on which the option contracts are based.
    expiration: Date on which the option contract expires; must be a valid expiration date. Defaults to the next contract expiration date.
    expiration2: Second contract expiration date required for Calendar and Diagonal spreads.
    strike_proximity: Specifies the number of spreads to display above and below the priceCenter.
    spread_type: Specifies the name of the spread type to use.
    risk_free_rate: The theoretical rate of return of an investment with zero risk. Defaults to the current quote for $IRX.X. The percentage rate should be specified as a decimal value. For example, to use 2% for the rate, pass in 0.02.
    price_center: Specifies the strike price center. Defaults to the last quoted price for the underlying security.
    strike_interval: Specifies the desired interval between the strike prices in a spread. It must be greater than or equal to 1. A value of 1 uses consecutive strikes; a value of 2 skips one between strikes; and so on.
    enable_greeks: Specifies whether or not greeks properties are returned.
    strike_range: * If the filter is `ITM` (in-the-money), the chain includes only spreads that have an intrinsic value greater than zero.\n* If the filter is `OTM` (out-of-the-money), the chain includes only spreads that have an intrinsic value equal to zero.
    option_type: Filters the spreads by a specific option type. Valid values are `All`, `Call`, and `Put`."""
        url = f"{self.base_url}/v3/marketdata/stream/options/chains/{underlying}"
        response = await self.client.get(url, params={k: v for k, v in {'expiration': expiration, 'expiration2': expiration2, 'strikeProximity': strike_proximity, 'spreadType': spread_type, 'riskFreeRate': risk_free_rate, 'priceCenter': price_center, 'strikeInterval': strike_interval, 'enableGreeks': enable_greeks, 'strikeRange': strike_range, 'optionType': option_type}.items() if v is not None})
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 429, 503, 504}:
            if response.status_code == 200: return Spread.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_option_quotes(self, legs_0_symbol: str, legs_0_ratio: Optional[float] = 1, risk_free_rate: Optional[float] = None, enable_greeks: Optional[bool] = True) -> Union[ErrorResponse, Spread]:
        """Stream Option Quotes

Args:
    legs_0_symbol: * `legs`: Individual components of a multi-part trade.\n* `[0]`: Represents the position in the legs array.\n* `Symbol`: Option contract symbol or underlying symbol to be traded for this leg. In some cases, the space in an option symbol may need to be explicitly URI encoded as %20, such as `MSFT%20220916C305`.
    legs_0_ratio: * `legs`: Individual components of a multi-part trade.\n* `[0]`: Represents the position in the legs array.\n* `Ratio`: The number of option contracts or underlying shares for this leg, relative to the other legs. Use a positive number to represent a buy trade and a negative number to represent a sell trade. For example, a quote for a Butterfly spread can be requested using ratios of 1, -2, and 1: buy 1 contract of the first leg, sell 2 contracts of the second leg, and buy 1 contract of the third leg.
    risk_free_rate: The theoretical rate of return of an investment with zero risk. Defaults to the current quote for $IRX.X. The percentage rate should be specified as a decimal value. For example, to use 2% for the rate, pass in 0.02.
    enable_greeks: Specifies whether or not greeks properties are returned."""
        url = f"{self.base_url}/v3/marketdata/stream/options/quotes"
        response = await self.client.get(url, params={k: v for k, v in {'legs[0].Symbol': legs_0_symbol, 'legs[0].Ratio': legs_0_ratio, 'riskFreeRate': risk_free_rate, 'enableGreeks': enable_greeks}.items() if v is not None})
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 429, 503, 504}:
            if response.status_code == 200: return Spread.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_quote_snapshots(self, symbols: str) -> Union[ErrorResponse, QuoteSnapshot]:
        """Get Quote Snapshots

Args:
    symbols: List of valid symbols in comma separated format; for example `\"MSFT,BTCUSD\"`. No more than 100 symbols per request."""
        url = f"{self.base_url}/v3/marketdata/quotes/{symbols}"
        response = await self.client.get(url, )
        response.raise_for_status()
        if response.status_code in {200, 400, 401, 403, 404, 429, 503, 504}:
            if response.status_code == 200: return QuoteSnapshot.from_dict(response.json())
            if response.status_code == 400: return ErrorResponse.from_dict(response.json())
            if response.status_code == 401: return ErrorResponse.from_dict(response.json())
            if response.status_code == 403: return ErrorResponse.from_dict(response.json())
            if response.status_code == 404: return ErrorResponse.from_dict(response.json())
            if response.status_code == 429: return ErrorResponse.from_dict(response.json())
            if response.status_code == 503: return ErrorResponse.from_dict(response.json())
            if response.status_code == 504: return ErrorResponse.from_dict(response.json())
        raise ValueError('Unexpected response status code: {response.status_code}')
    
    async def get_quote_change_stream(self, symbols: str) -> AsyncGenerator[Union[Heartbeat, QuoteStream, StreamErrorResponse], None]:
        """Stream Quotes

Args:
    symbols: List of valid symbols in comma separated format; for example `\"MSFT,BTCUSD\"`. No more than 100 symbols per request."""
        url = f"{self.base_url}/v3/marketdata/stream/quotes/{symbols}"
        async with self.client.stream('GET', url) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    # skip malformed lines
                    continue
                try:
                    yield Heartbeat1.from_dict(obj)
                    continue
                except Exception:
                    pass
                try:
                    yield QuoteStream.from_dict(obj)
                    continue
                except Exception:
                    pass
                try:
                    yield StreamErrorResponse.from_dict(obj)
                    continue
                except Exception:
                    pass
                # fallback: yield raw dict
                yield obj
    
    async def stream_market_depth_quotes(self, symbol: str, maxlevels: Optional[int] = 20) -> AsyncGenerator[Union[Heartbeat2, MarketDepthQuote, StreamErrorResponse], None]:
        """
        Stream Market Depth Quotes

        Args:
            symbol: A valid symbol for the security.
            maxlevels: The maximum number of market depth levels to return. Must be a positive integer. If omitted it defaults to 20.
        """
        url = f"{self.base_url}/v3/marketdata/stream/marketdepth/quotes/{symbol}"
        async with self.client.stream('GET', url, params={k: v for k, v in {'maxlevels': maxlevels}.items() if v is not None}) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    # skip malformed lines
                    continue
                try:
                    yield Heartbeat2.from_dict(obj)
                    continue
                except Exception:
                    pass
                try:
                    yield MarketDepthQuote.from_dict(obj)
                    continue
                except Exception:
                    pass
                try:
                    yield StreamErrorResponse.from_dict(obj)
                    continue
                except Exception:
                    pass
                # fallback: yield raw dict
                yield obj
    
    async def stream_market_depth_aggregates(self, symbol: str, maxlevels: Optional[int] = 20) -> AsyncGenerator[Union[Heartbeat2, MarketDepthAggregate, StreamErrorResponse], None]:
        """
        Stream Market Depth Aggregates

        Args:
            symbol: A valid symbol for the security.
        Args:
            maxlevels: The maximum number of market depth levels to return. Must be a positive integer. If omitted it defaults to 20.
        """
        url = f"{self.base_url}/v3/marketdata/stream/marketdepth/aggregates/{symbol}"
        async with self.client.stream('GET', url, params={k: v for k, v in {'maxlevels': maxlevels}.items() if v is not None}) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    # skip malformed lines
                    continue
                try:
                    yield Heartbeat2.from_dict(obj)
                    continue
                except Exception:
                    pass
                try:
                    yield MarketDepthAggregate.from_dict(obj)
                    continue
                except Exception:
                    pass
                try:
                    yield StreamErrorResponse.from_dict(obj)
                    continue
                except Exception:
                    pass
                # fallback: yield raw dict
                yield obj
    
    async def stream_orders(self, accounts: str) -> AsyncGenerator[Union[Heartbeat, Order, StreamOrderErrorResponse, StreamStatus], None]:
        """
        Stream Orders

        Args:
            accounts: List of valid Account IDs for the authenticated user in comma separated format; for example `\"61999124,68910124\"`. 1 to 25 Account IDs can be specified, comma separated.
        """
        url = f"{self.base_url}/v3/brokerage/stream/accounts/{accounts}/orders"
        async with self.client.stream('GET', url) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    # skip malformed lines
                    continue
                yield TypeAdapter(Union[Order, Heartbeat, StreamOrderErrorResponse, StreamStatus]).validate_python(obj)
    
    async def stream_orders_by_order_id(self, accounts: str, orders_ids: str) -> AsyncGenerator[Union[Heartbeat, Order, StreamOrderByOrderIdErrorResponse, StreamStatus], None]:
        """
        Stream Orders by Order Id

        Args:
            accounts: List of valid Account IDs for the authenticated user in comma separated format; for example `\"61999124,68910124\"`. 1 to 25 account IDs can be specified, comma separated.
            orders_ids: List of valid Order IDs for the account IDs in comma separated format; for example `\"812767578,812941051\"`. 1 to 50 order IDs can be specified, comma separated.
        """
        url = f"{self.base_url}/v3/brokerage/stream/accounts/{accounts}/orders/{orders_ids}"
        async with self.client.stream('GET', url) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    # skip malformed lines
                    continue
                try:
                    yield Heartbeat3.from_dict(obj)
                    continue
                except Exception:
                    pass
                try:
                    yield Order1.from_dict(obj)
                    continue
                except Exception:
                    pass
                try:
                    yield StreamOrderByOrderIdErrorResponse.from_dict(obj)
                    continue
                except Exception:
                    pass
                try:
                    yield StreamStatus.from_dict(obj)
                    continue
                except Exception:
                    pass
                # fallback: yield raw dict
                yield obj
    
    async def stream_positions(self, accounts: str, changes: Optional[bool] = False) -> AsyncGenerator[Union[Heartbeat, Position, StreamPositionsErrorResponse, StreamStatus], None]:
        """Stream Positions

        Args:
            accounts: List of valid Account IDs for the authenticated user in comma separated format; for example `\"61999124,68910124\"`. 1 to 25 Account IDs can be specified, comma separated.
        Args:
            changes: A boolean value that specifies whether or not position updates are streamed as changes. When a stream is first opened with `\"changes=true\"`, streaming positions will return the full snapshot first for all positions, and then any changes after that. When `\"changes=true\"`, the PositionID field is returned with each change, along with the fields that changed."""
        url = f"{self.base_url}/v3/brokerage/stream/accounts/{accounts}/positions"
        async with self.client.stream('GET', url, params={k: v for k, v in {'changes': changes}.items() if v is not None}) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    # skip malformed lines
                    continue
                try:
                    yield Heartbeat3.from_dict(obj)
                    continue
                except Exception:
                    pass
                try:
                    yield Position.from_dict(obj)
                    continue
                except Exception:
                    pass
                try:
                    yield StreamPositionsErrorResponse.from_dict(obj)
                    continue
                except Exception:
                    pass
                try:
                    yield StreamStatus.from_dict(obj)
                    continue
                except Exception:
                    pass
                # fallback: yield raw dict
                yield obj
