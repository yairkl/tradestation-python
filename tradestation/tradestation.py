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
from .types import (
    Order, OrderRequest, TrailingStop, OrderError, Account,
    OrderRequestOSO, AdvancedOptions, Bar, Heartbeat, Error, ErrorResponse
)

AUTH_URL = "https://signin.tradestation.com/authorize"
TOKEN_URL = "https://signin.tradestation.com/oauth/token"
LIVE_API_URL = "https://api.tradestation.com/v3"
DEMO_API_URL = "https://sim-api.tradestation.com/v3"
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

class TradeStation:
    """Handles authentication and API requests for TradeStation."""
    ### Initiation and Authentication handling ###
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, port: int = 8080,
                 is_demo: bool = True, refresh_token_margin:float=60, async_mode: bool = False):
        self.client_id = client_id if client_id else os.getenv('CLIENT_ID')
        self.client_secret = client_secret if client_secret else os.getenv('CLIENT_SECRET')
        assert self.client_id, "Either client_id or CLIENT_ID environment variable must be provided."
        assert self.client_secret, "Either client_secret or CLIENT_SECRET environment variable must be provided."
        self.port=port
        self.api_url = DEMO_API_URL if is_demo else LIVE_API_URL
        self.redirect_uri = f'http://localhost:{self.port}/'
        self.access_token = None
        self.refresh_token = None
        self.expires_in = None
        self.refresh_margin = timedelta(seconds=refresh_token_margin)
        if async_mode:
            self.auth_code_event = asyncio.Event()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._async_authenticate())
        else:
            self._authenticate()
            
        # self.refresh_task = loop.create_task(self._refresh_token_loop())

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

    async def _start_async_server(self):
        app = web.Application()
        app.router.add_get("/", self._handle_auth_redirect)
        runner = web.AppRunner(app)
        await runner.setup()
        self.server = web.TCPSite(runner, "localhost", self.port)
        await self.server.start()

    async def _stop_async_server(self):
        await self.server.stop()

    async def _handle_auth_redirect(self, request):
        query = request.rel_url.query
        code = query.get("code")
        if code:
            await self._async_exchange_code_for_token(code)
            self.auth_code_event.set()
            return web.Response(body=auth_success_html, content_type='text/html')
        return web.Response(text="No authorization code found.")

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

    async def _async_exchange_code_for_token(self, code:str):
        """Exchanges the authorization code for an access token."""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        async with httpx.AsyncClient() as client:
            response = await client.post(TOKEN_URL, data=data, headers=headers)
            if response.status_code == 200:
                body = response.json()
                self.access_token = body['access_token']
                self.refresh_token = body['refresh_token']
                self.token_expiry = datetime.now() + timedelta(seconds=body.get('expires_in', 1200))
            else:
                raise ValueError(f"Error obtaining token: {response.text}")

    async def _refresh_token_loop(self) -> None:
        """
        Periodically refreshes the access token before it expires.

        :raises ValueError: If no refresh token is available or the refresh request fails.
        """
        while True:
            if not self.refresh_token:
                print("No refresh token available.")
                return

            now = datetime.now()
            refresh_in = self.token_expiry - now - self.refresh_margin
            refresh_in = max(refresh_in.seconds, 0)
            print(f"Refreshing token in {refresh_in:.1f} seconds")
            await asyncio.sleep(refresh_in)
            print("Refreshing access token...")
            await self._refresh_access_token()
    
    async def _refresh_access_token(self) -> None:
        """
        Refreshes the access token using the refresh token.

        :raises ValueError: If no refresh token is available or the refresh request fails.
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = await self._asend_request(url=TOKEN_URL, data=data, headers=headers)
        if response.status_code == 200:
            body = response.json()
            self.access_token = body['access_token']
            self.token_expiry = datetime.now() + timedelta(seconds=body.get('expires_in', 1200))
        else:
            raise ValueError(f"Error refreshing token: {response.text}")

    def _authenticate(self):
        """Handles the authentication flow."""
        self._start_server()
        webbrowser.open(self._generate_auth_url())
        
        while self.access_token is None:
            pass

    async def _async_authenticate(self):
        await self._start_async_server()
        webbrowser.open(self._generate_auth_url())
        # Wait for the first auth to complete
        await self.auth_code_event.wait()
        await self._stop_async_server()
    
    def _send_request(self, 
                      endpoint: str, 
                      params: Optional[dict] = None, 
                      method: Literal['GET', 'POST', 'PUT', 'DELETE'] = 'GET', 
                      headers: Optional[dict] = None, 
                      payload: Optional[dict] = None) -> dict:
        """
        Sends a synchronous HTTP request to the TradeStation API.

        :param endpoint: The API endpoint to send the request to.
        :param params: Query parameters to include in the request.
        :param method: HTTP method to use for the request. Valid values are 'GET', 'POST', 'PUT', 'DELETE'.
        :param headers: Optional headers to include in the request. If not provided, default headers with authorization will be used.
        :param payload: Optional JSON payload to include in the request body.
        :return: A dictionary containing the JSON response from the API.
        :raises ValueError: If the request fails or invalid data is received.
        """
        url = f"{self.api_url}/{endpoint}"
        if not headers:
            headers = {"Authorization": f"Bearer {self.access_token}"}
        with httpx.Client() as client:
            response = client.request(method, url, headers=headers, params=params, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            request_error = ErrorResponse.from_dict(ErrorResponse)
            raise ValueError(f"Request failed with status code {response.status_code} and error: \"{request_error.error}\" with message: \"{request_error.message}\"")

    async def _asend_request(self, 
                             endpoint: Optional[str] = None, 
                             url: Optional[str] = None, 
                             params: Optional[dict] = None, 
                             method: Literal['GET', 'POST', 'PUT', 'DELETE'] = 'GET', 
                             headers: Optional[dict] = None, 
                             payload: Optional[dict] = None) -> dict:
        """
        Sends an asynchronous HTTP request to the TradeStation API.

        :param endpoint: The API endpoint to send the request to. Either `endpoint` or `url` must be provided.
        :param url: The full URL to send the request to. Overrides `endpoint` if provided.
        :param params: Query parameters to include in the request.
        :param method: HTTP method to use for the request. Valid values are 'GET', 'POST', 'PUT', 'DELETE'.
        :param headers: Optional headers to include in the request. If not provided, default headers with authorization will be used.
        :param payload: Optional JSON payload to include in the request body.
        :return: A dictionary containing the JSON response from the API.
        :raises ValueError: If the request fails or invalid parameters are provided.
        """
        if not url:
            if not endpoint:
                raise ValueError("Either endpoint or url must be provided.")
            url = f"{self.api_url}/{endpoint}"

        if not headers and self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, params=params, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError(f"Request failed with status code {response.status_code} and message: \"{response.text}\"")

    def _stream_request(self, 
                        endpoint: str, 
                        params: Optional[dict] = None, 
                        method: Literal['GET', 'POST', 'PUT', 'DELETE'] = 'GET', 
                        headers: Optional[dict] = None, 
                        payload: Optional[dict] = None, 
                        timeout: Union[int, float] = 10) -> Generator[dict, None, None]:
        """
        Streams a synchronous HTTP request to the TradeStation API.

        :param endpoint: The API endpoint to send the request to.
        :param params: Query parameters to include in the request.
        :param method: HTTP method to use for the request. Valid values are 'GET', 'POST', 'PUT', 'DELETE'.
        :param headers: Optional headers to include in the request. If not provided, default headers with authorization will be used.
        :param payload: Optional JSON payload to include in the request body.
        :param timeout: Timeout for the request in seconds.
        :return: A generator yielding parsed JSON data from the stream.
        :raises ValueError: If the request fails or invalid data is received.
        """
        url = f"{self.api_url}/{endpoint}"
        if not headers and self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}

        with httpx.stream(method, url, headers=headers, params=params, json=payload, timeout=timeout) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            yield data
                        except json.JSONDecodeError:
                            raise ValueError(f"Invalid JSON received: {line}")
            else:
                raise ValueError(f"Request failed with status code {response.status_code} and message: \"{response.read().decode()}\"")
    
    async def _astream_request(self, 
                               endpoint: str, 
                               params: Optional[dict] = None, 
                               method: Literal['GET', 'POST', 'PUT', 'DELETE'] = 'GET', 
                               headers: Optional[dict] = None, 
                               payload: Optional[dict] = None, 
                               timeout: Union[int, float] = 10) -> AsyncGenerator[dict, None]:
        """
        Streams an asynchronous HTTP request to the TradeStation API.

        :param endpoint: The API endpoint to send the request to.
        :param params: Query parameters to include in the request.
        :param method: HTTP method to use for the request. Valid values are 'GET', 'POST', 'PUT', 'DELETE'.
        :param headers: Optional headers to include in the request. If not provided, default headers with authorization will be used.
        :param payload: Optional JSON payload to include in the request body.
        :param timeout: Timeout for the request in seconds.
        :return: An asynchronous generator yielding parsed JSON data from the stream.
        :raises ValueError: If the request fails or invalid data is received.
        """
        url = f"{self.api_url}/{endpoint}"
        if not headers and self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with httpx.AsyncClient() as client:
            async with client.stream(method, url, headers=headers, params=params, json=payload, timeout=timeout) as response:
                if response.status_code == 200:
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                yield data
                            except json.JSONDecodeError:
                                raise ValueError(f"Invalid JSON received: {line}")
                else:
                    raise ValueError(f"Request failed with status code {response.status_code} and message: \"{await response.aread()}\"")

    ### Market Data ###
    
    def get_historical_data(self, 
                 symbol: str, 
                 interval: int = 1, 
                 unit: Literal['Minute', 'Daily', 'Weekly', 'Monthly'] = 'Daily', 
                 bars_back: Optional[int] = None, 
                 first_date: Optional[datetime] = None, 
                 last_date: Optional[datetime] = None,
                 session_template: Literal['USEQPre', 'USEQPost', 'USEQPreAndPost', 'USEQ24Hour', 'Default'] = 'Default'):
        """Fetches historical market data bars from TradeStation."""
        if bars_back and first_date:
            raise ValueError("bars_back and first_date should be mutually exclusive. Choose one.")
        if not bars_back and not first_date:
            bars_back = 1
        
        params = {
            'interval': interval,
            'unit': unit,
            'sessiontemplate': session_template
        }
        if first_date:
            params['firstdate'] = first_date.replace(microsecond=0).astimezone(timezone.utc).isoformat()
        else:
            params['barsback'] = bars_back
        
        if last_date:
            params['lastdate'] = last_date.replace(microsecond=0).astimezone(timezone.utc).isoformat()
        bars = (Bar.from_dict(b) for b in self._send_request(f"marketdata/barcharts/{symbol}", params).get('Bars', []))
        return bars
    
    async def aget_historical_data(self, 
                                symbol: str, 
                                interval: int = 1, 
                                unit: Literal['Minute', 'Daily', 'Weekly', 'Monthly'] = 'Daily', 
                                bars_back: Optional[int] = None, 
                                first_date: Optional[datetime] = None, 
                                last_date: Optional[datetime] = None,
                                session_template: Literal['USEQPre', 'USEQPost', 'USEQPreAndPost', 'USEQ24Hour', 'Default'] = 'Default'):
        """Fetches historical market data bars from TradeStation."""
        if bars_back and first_date:
            raise ValueError("bars_back and first_date should be mutually exclusive. Choose one.")
        if not bars_back and not first_date:
            bars_back = 1
        
        params = {
            'interval': interval,
            'unit': unit,
            'sessiontemplate': session_template
        }
        if first_date:
            params['firstdate'] = first_date.replace(microsecond=0).astimezone(timezone.utc).isoformat()
        else:
            params['barsback'] = bars_back
        
        if last_date:
            params['lastdate'] = last_date.replace(microsecond=0).astimezone(timezone.utc).isoformat()
        res = await self._asend_request(f"marketdata/barcharts/{symbol}", params)
        bars = (Bar.from_dict(b) for b in res.get('Bars', []))
        return bars

    def stream_tick_bars(self,
                         symbol: str, 
                         unit: Literal['Minute', 'Daily', 'Weekly', 'Monthly'] = 'Daily', 
                         interval: int = 1,
                         bars_back: int = None,
                         session_template: Literal['USEQPre', 'USEQPost', 'USEQPreAndPost', 'USEQ24Hour', 'Default'] = 'Default') -> Generator[dict, None, None]:
        """
        Streams tick bars data for the specified symbol.

        :param symbol: The symbol to stream data for.
        :param interval: Interval for each bar one of: 'Minute', 'Daily', 'Weekly', 'Monthly'.
        :param bars_back: Number of bars to retrieve.
        :param session_template: Session template for the data stream.
        :return: A generator yielding parsed JSON data from the stream, the data can be one of the following:
            - "Heartbeat": Heartbeat message indicating the stream is alive.
            - "Error": Error message indicating an issue with the stream.
            - Tick bar data: Actual tick bar data for the specified symbol.
        """

        # Validate inputs
        if not (1 <= interval <= 64999):
            raise ValueError("Interval must be between 1 and 64999 ticks.")
        if bars_back and not (1 <= bars_back <= 57600):
            raise ValueError("BarsBack must be between 1 and 57600.")

        params = {
            "interval":interval,
            "unit":unit,
            'sessiontemplate': session_template
        }
        if bars_back:
            params['barsback'] = bars_back
        
        stream_generator = self._stream_request(f"marketdata/stream/barcharts/{symbol}", params=params)
        return (Error.from_dict(d) if "Error" in d else Heartbeat.from_dict(d) if "Heartbeat" in d else Bar.from_dict(d) for d in stream_generator)
    
    async def astream_tick_bars(self,
                               symbol: str, 
                               unit: Literal['Minute', 'Daily', 'Weekly', 'Monthly'] = 'Daily', 
                               interval: int = 1,
                               bars_back: int = None,
                               session_template: Literal['USEQPre', 'USEQPost', 'USEQPreAndPost', 'USEQ24Hour', 'Default'] = 'Default',
                               data_handler: Optional[callable] = None,
                               error_handler: Optional[callable] = None,
                               heartbeat_handler: Optional[callable] = None) -> Union[AsyncGenerator[dict, None], None]:
        """
        Asynchronously streams tick bars data for the specified symbol.

        :param symbol: The symbol to stream data for.
        :param unit: Interval unit ('Minute', 'Daily', 'Weekly', 'Monthly').
        :param interval: Interval for each bar.
        :param bars_back: Number of bars to retrieve.
        """

        # Validate inputs
        if not (1 <= interval <= 64999):
            raise ValueError("Interval must be between 1 and 64999 ticks.")
        if bars_back and not (1 <= bars_back <= 57600):
            raise ValueError("BarsBack must be between 1 and 57600.")

        # Construct the HTTP SSE URL
        params = {
            "interval": interval,
            "unit": unit,
            "sessiontemplate": session_template
        }
        if bars_back:
            params["barsback"] = bars_back

        data_generator = self._astream_request(f"marketdata/stream/barcharts/{symbol}", params=params)
        if not data_handler:
            return (Error.from_dict(d) if "Error" in d else Heartbeat.from_dict(d) if "Heartbeat" in d else Bar.from_dict(d) async for d in data_generator)
        async for data in data_generator:
            if data:
                if "Heartbeat" in data:
                    if heartbeat_handler:
                        heartbeat_handler(data)
                elif "Error" in data:
                    if error_handler:
                        error_handler(data)
                else:
                    data_handler(data)
            else:
                if error_handler:
                    error_handler({"Error": "InvalidData",
                                "Message": "Received empty data from the stream."})
                else:
                    raise ValueError("Received empty data from the stream.")

    ### Brokerage services ###
    
    def get_accounts(self):
        return [Account.from_dict(a) for a in self._send_request("brokerage/accounts").get("Accounts", [])]
    
    async def aget_accounts(self):
        data = await self._asend_request("brokerage/accounts")
        return [Account.from_dict(a) for a in data.get("Accounts", [])]

    def get_balances(self, accounts:Union[str, Account, List[str], List[Account]]):
        """Fetches account balances for the specified accounts."""
        if isinstance(accounts, str) or isinstance(accounts, Account):
            accounts = [accounts]
        accounts = [a.account_ID if isinstance(a, Account) else a for a in accounts]
        accounts = ",".join(accounts)
        return self._send_request(f"brokerage/accounts/{accounts}/balances")
    
    async def aget_balances(self, accounts:Union[str, List[str]]):
        """Fetches account balances for the specified accounts asynchronously."""
        if isinstance(accounts, str):
            accounts = [accounts]
        accounts = ",".join(accounts)
        return await self._asend_request(f"brokerage/accounts/{accounts}/balances")
    
    def get_historical_orders(self, accounts:Union[str, List[str]], since: datetime) -> Tuple[Generator[Order, None, None], Generator[OrderError, None, None]]:
        """
        Fetches historical orders and open orders for the given Accounts since given date
        sorted in descending order of time placed for open and time executed for closed.
        Request valid for all account types.
        """

        if isinstance(accounts, str):
            accounts = [accounts]
        accounts = ",".join(accounts)
        res = self._send_request(f"brokerage/accounts/{accounts}/historicalorders", params={"since":since.replace(microsecond=0).astimezone(timezone.utc).isoformat()})
        orders = (Order.from_dict(d) for d in res.get('Orders', []))
        errors = (OrderError.from_dict(d) for d in res.get('Errors', []))
        return orders, errors
    
    def get_orders(self, accounts:Union[str, List[str]]) -> Tuple[Generator[Order, None, None], Generator[OrderError, None, None]]:
        """
        Fetches today's orders and open orders for the given Accounts, 
        sorted in descending order of time placed for open and time executed for closed.
        Request valid for all account types.
        """

        if isinstance(accounts, str):
            accounts = [accounts]
        accounts = ",".join(accounts)
        res = self._send_request(f"brokerage/accounts/{accounts}/orders")
        orders = (Order.from_dict(d) for d in res.get('Orders', []))
        errors = (OrderError.from_dict(d) for d in res.get('Errors', []))
        return orders, errors

    async def aget_orders(self, accounts:Union[str, List[str]]):
        """
        Fetches today's orders and open orders for the given Accounts, 
        sorted in descending order of time placed for open and time executed for closed.
        Request valid for all account types.
        """
        if isinstance(accounts, str):
            accounts = [accounts]
        accounts = ",".join(accounts)
        return await self._asend_request(endpoint=f"brokerage/accounts/{accounts}/orders")
    
    def get_order_by_id(self, accounts:Union[str, List[str]], order_ids:Union[str, List[str]]):
        """
        Fetches today's orders and open orders for the given Accounts, 
        filtered by given Order IDs, sorted in descending order of time placed for open and time executed for closed.
        Request valid for all account types.
        """
        if isinstance(accounts, str):
            accounts = [accounts]
        if isinstance(order_ids, str):
            order_ids = [order_ids] 
        accounts = ",".join(accounts)
        order_ids= ",".join(order_ids)
        return self._send_request(f"brokerage/accounts/{accounts}/orders/{order_ids}")
    
    async def aget_order_by_id(self, accounts:Union[str, List[str]], order_ids:Union[str, List[str]]):
        """
        Asynchronously fetches today's orders and open orders for the given Accounts, 
        filtered by given Order IDs, sorted in descending order of time placed for open and time executed for closed.
        Request valid for all account types.
        """
        if isinstance(accounts, str):
            accounts = [accounts]
        if isinstance(order_ids, str):
            order_ids = [order_ids] 
        accounts = ",".join(accounts)
        order_ids= ",".join(order_ids)
        return await self._asend_request(f"brokerage/accounts/{accounts}/orders/{order_ids}")

    def get_positions(self, accounts: Union[str, List[str]], symbol: Optional[Union[str, List[str]]] = None):
        """
        Fetches positions for the given Accounts. Request valid for Cash, Margin, Futures, and DVP account types.

        :param accounts: List of valid Account IDs for the authenticated user in comma-separated format.
        :param symbol: Optional. List of valid symbols in comma-separated format. Supports wildcards for filtering.
        """
        if isinstance(accounts, str):
            accounts = [accounts]
        accounts = ",".join(accounts)

        params = {}
        if symbol:
            if isinstance(symbol, str):
                symbol = [symbol]
            params['symbol'] = ",".join(symbol)

        return self._send_request(f"brokerage/accounts/{accounts}/positions", params=params)

    async def aget_positions(self, accounts: Union[str, List[str]], symbol: Optional[Union[str, List[str]]] = None):
        """
        Asynchronously fetches positions for the given Accounts. Request valid for Cash, Margin, Futures, and DVP account types.

        :param accounts: List of valid Account IDs for the authenticated user in comma-separated format.
        :param symbol: Optional. List of valid symbols in comma-separated format. Supports wildcards for filtering.
        """
        if isinstance(accounts, str):
            accounts = [accounts]
        accounts = ",".join(accounts)

        params = {}
        if symbol:
            if isinstance(symbol, str):
                symbol = [symbol]
            params['symbol'] = ",".join(symbol)

        return await self._asend_request(f"brokerage/accounts/{accounts}/positions", params=params)

    async def astream_positions(self, accounts: Union[str, List[str]], 
                                 changes: bool = False,
                                 data_handler: Optional[callable] = None, 
                                 error_handler: Optional[callable] = None,
                                 heartbeat_handler: Optional[callable] = None,
                                 status_handler: Optional[callable] = None,
                                 deleted_handler: Optional[callable] = None) -> Union[AsyncGenerator[dict, None], None]:
        """
        Streams positions for the given accounts asynchronously. Request valid for Cash, Margin, Futures, and DVP account types.
        :param accounts: List of valid Account IDs for the authenticated user in comma-separated format.
        :param changes: Boolean value to specify whether to stream updates as changes.
        :param data_handler: Function to handle incoming position data.
        :param error_handler: Function to handle errors.
        :param heartbeat_handler: Function to handle heartbeat messages.
        :param status_handler: Function to handle stream status messages.
        :param deleted_handler: Function to handle deleted messages.
        :return: An asynchronous generator yielding parsed JSON data from the stream, the data can be one of the following:
            - "Heartbeat": Heartbeat message indicating the stream is alive.
            - "Error": Error message indicating an issue with the stream.
            - "StreamStatus": Status message indicating the current state of the stream.
            - "Deleted": Message indicating that a position has been deleted.
            - Position data: Actual position data for the specified accounts.
        """
        if isinstance(accounts, str):
            accounts = [accounts]
        accounts = ",".join(accounts)

        params = {"changes": str(changes).lower()}

        data_generator = self._astream_request(endpoint=f"brokerage/stream/accounts/{accounts}/positions", params=params)
        if not data_handler:
            return data_generator
        async for data in self._astream_request(endpoint=f"brokerage/stream/accounts/{accounts}/positions", params=params):
            if data:
                if "Heartbeat" in data:
                    heartbeat_handler(data)
                elif "Error" in data:
                    error_handler(data)
                elif "StreamStatus" in data:
                    status_handler(data)
                elif "Deleted" in data:
                    deleted_handler(data)

                else:
                    data_handler(data)
            else:
                error_handler({"Error": "InvalidData",
                               "Message": "Received empty data from the stream."})

    def stream_positions(self, accounts: Union[str, List[str]], 
                         changes: bool = False,
                         data_handler=print, 
                         error_handler=print, 
                         heartbeat_handler=lambda x: None,
                         status_handler=print,
                         deleted_handler=print):
        """
        Streams positions for the given accounts synchronously. Request valid for Cash, Margin, Futures, and DVP account types.

        :param accounts: List of valid Account IDs for the authenticated user in comma-separated format.
        :param changes: Boolean value to specify whether to stream updates as changes.
        :param data_handler: Function to handle incoming position data.
        :param error_handler: Function to handle errors.
        :param heartbeat_handler: Function to handle heartbeat messages.
        :param status_handler: Function to handle stream status messages.
        :param deleted_handler: Function to handle deleted messages.
        """
        if isinstance(accounts, str):
            accounts = [accounts]
        accounts = ",".join(accounts)

        params = {"changes": str(changes).lower()}

        for data in self._stream_request(endpoint=f"brokerage/stream/accounts/{accounts}/positions", params=params):
            if data:
                if "Heartbeat" in data:
                    heartbeat_handler(data)
                elif "Error" in data:
                    error_handler(data)
                elif "StreamStatus" in data:
                    status_handler(data)
                elif "Deleted" in data:
                    deleted_handler(data)
                else:
                    data_handler(data)
            else:
                error_handler({"Error": "InvalidData",
                               "Message": "Received empty data from the stream."})

    async def astream_orders(self, accounts: Union[str, List[str]], 
                            data_handler=print, 
                            error_handler=print, 
                            heartbeat_handler=lambda x: None,
                            status_handler=print):
        """
        Streams orders for the given accounts. Request valid for Cash, Margin, Futures, and DVP account types.

        :param accounts: List of valid Account IDs for the authenticated user.
        :param data_handler: Function to handle incoming order data.
        :param error_handler: Function to handle errors.
        :param heartbeat_handler: Function to handle heartbeat messages.
        :param status_handler: Function to handle stream status messages.
        """
        if isinstance(accounts, str):
            accounts = [accounts]
        accounts = ",".join(accounts)

        async for data in self._astream_request(endpoint=f"brokerage/stream/accounts/{accounts}/orders"):
            if data:
                try:
                    if "Heartbeat" in data:
                        heartbeat_handler(data)
                    elif "Error" in data:
                        error_handler(data)
                    elif "StreamStatus" in data:
                        status_handler(data)
                    else:
                        data_handler(data)
                except json.JSONDecodeError:
                    error_handler({"Error": "InvalidJSON",
                                   "Message": f"The received data is not a valid JSON: \"{data}\""})

    async def astream_orders_by_id(self, accounts: Union[str, List[str]], order_ids: Union[str, List[str]], 
                                  data_handler=print, 
                                  error_handler=print, 
                                  heartbeat_handler=lambda x: None,
                                  status_handler=print):
        """
        Streams orders for the given accounts and order IDs. Request valid for Cash, Margin, Futures, and DVP account types.

        :param accounts: List of valid Account IDs for the authenticated user in comma-separated format.
        :param order_ids: List of valid Order IDs for the account IDs in comma-separated format.
        :param data_handler: Function to handle incoming order data.
        :param error_handler: Function to handle errors.
        :param heartbeat_handler: Function to handle heartbeat messages.
        :param status_handler: Function to handle stream status messages.
        """
        if isinstance(accounts, str):
            accounts = [accounts]
        if isinstance(order_ids, str):
            order_ids = [order_ids]
        accounts = ",".join(accounts)
        order_ids = ",".join(order_ids)

        async for data in self._astream_request(endpoint=f"brokerage/stream/accounts/{accounts}/orders/{order_ids}"):
            if data:
                try:
                    if "Heartbeat" in data:
                        heartbeat_handler(data)
                    elif "Error" in data:
                        error_handler(data)
                    elif "StreamStatus" in data:
                        status_handler(data)
                    else:
                        data_handler(data)
                except json.JSONDecodeError:
                    error_handler({"Error": "InvalidJSON",
                                   "Message": f"The received data is not a valid JSON: \"{data}\""})

    def stream_orders(self, accounts: Union[str, List[str]], 
                      data_handler=print, 
                      error_handler=print, 
                      heartbeat_handler=lambda x: None,
                      status_handler=print):
        """
        Streams orders for the given accounts synchronously. Request valid for Cash, Margin, Futures, and DVP account types.

        :param accounts: List of valid Account IDs for the authenticated user in comma-separated format.
        :param data_handler: Function to handle incoming order data.
        :param error_handler: Function to handle errors.
        :param heartbeat_handler: Function to handle heartbeat messages.
        :param status_handler: Function to handle stream status messages.
        """
        if isinstance(accounts, str):
            accounts = [accounts]
        accounts = ",".join(accounts)

        for data in self._stream_request(endpoint=f"brokerage/stream/accounts/{accounts}/orders"):
            if "Heartbeat" in data:
                heartbeat_handler(data)
            elif "Error" in data:
                error_handler(data)
            elif "StreamStatus" in data:
                status_handler(data)
            else:
                data_handler(data)

    def stream_orders_by_id(self, accounts: Union[str, List[str]], order_ids: Union[str, List[str]], 
                            data_handler=print, 
                            error_handler=print, 
                            heartbeat_handler=lambda x: None,
                            status_handler=print):
        """
        Streams orders for the given accounts and order IDs synchronously. Request valid for Cash, Margin, Futures, and DVP account types.

        :param accounts: List of valid Account IDs for the authenticated user in comma-separated format.
        :param order_ids: List of valid Order IDs for the account IDs in comma-separated format.
        :param data_handler: Function to handle incoming order data.
        :param error_handler: Function to handle errors.
        :param heartbeat_handler: Function to handle heartbeat messages.
        """
        if isinstance(accounts, str):
            accounts = [accounts]
        if isinstance(order_ids, str):
            order_ids = [order_ids]
        accounts = ",".join(accounts)
        order_ids = ",".join(order_ids)

        for data in self._stream_request(endpoint=f"brokerage/stream/accounts/{accounts}/orders/{order_ids}"):
            if "Heartbeat" in data:
                heartbeat_handler(data)
            elif "Error" in data:
                error_handler(data)
            elif "StreamStatus" in data:
                status_handler(data)
            else:
                data_handler(data)

    ### Order execution services ###

    def place_order(self, order: OrderRequest):
        """
        Places a new brokerage order.

        :param order: An OrderRequest object representing the order to be placed.
        :return: Response from the TradeStation API.
        """
        payload = order.to_dict()
        return self._send_request(method="POST", endpoint="orderexecution/orders", payload=payload)

    async def aplace_order(self, order: OrderRequest):
        """
        Asynchronously places a new brokerage order.

        :param order: An OrderRequest object representing the order to be placed.
        :return: Response from the TradeStation API.
        """
        payload = order.to_dict()
        return await self._asend_request(method="POST", endpoint="orderexecution/orders", payload=payload)

    def place_group_order(self, group_type: Literal["BRK", "OCO", "NORMAL"], orders: List[OrderRequest]):
        """
        Places a group order (OCO, BRK, or NORMAL).

        :param group_type: The group order type. Valid values are: BRK, OCO, and NORMAL.
        :param orders: List of OrderRequest objects representing the orders in the group.
        :return: Response from the TradeStation API.
        """
        payload = {
            "Type": group_type,
            "Orders": [order.to_dict() for order in orders]
        }
        return self._send_request(method="POST", endpoint="orderexecution/ordergroups", payload=payload)

    async def aplace_group_order(self, group_type: Literal["BRK", "OCO", "NORMAL"], orders: List[OrderRequest]):
        """
        Asynchronously places a group order (OCO, BRK, or NORMAL).

        :param group_type: The group order type. Valid values are: BRK, OCO, and NORMAL.
        :param orders: List of OrderRequest objects representing the orders in the group.
        :return: Response from the TradeStation API.
        """
        payload = {
            "Type": group_type,
            "Orders": [order.to_dict() for order in orders]
        }
        return await self._asend_request(method="POST", endpoint="orderexecution/ordergroups", payload=payload)

    def confirm_order(self, order: OrderRequest):
        """
        Confirms an order and returns estimated cost and commission information.

        :param order: An OrderRequest object representing the order to be confirmed.
        :return: Response from the TradeStation API.
        """
        payload = order.to_dict()
        return self._send_request(method="POST", endpoint="orderexecution/orderconfirm", payload=payload)

    async def aconfirm_order(self, order: OrderRequest):
        """
        Asynchronously confirms an order and returns estimated cost and commission information.

        :param order: An OrderRequest object representing the order to be confirmed.
        :return: Response from the TradeStation API.
        """
        payload = order.to_dict()
        return await self._asend_request(method="POST", endpoint="orderexecution/orderconfirm", payload=payload)

    def confirm_group_order(self, group_type: Literal["BRK", "OCO", "NORMAL"], orders: List[OrderRequest]):
        """
        Confirms a group order and returns estimated cost and commission information.

        :param group_type: The group order type. Valid values are: BRK, OCO, and NORMAL.
        :param orders: List of OrderRequest objects representing the orders in the group.
        :return: Response from the TradeStation API.
        """
        payload = {
            "Type": group_type,
            "Orders": [order.to_dict() for order in orders]
        }
        return self._send_request(method="POST", endpoint="orderexecution/ordergroupconfirm", payload=payload)

    async def aconfirm_group_order(self, group_type: Literal["BRK", "OCO", "NORMAL"], orders: List[OrderRequest]):
        """
        Asynchronously confirms a group order and returns estimated cost and commission information.

        :param group_type: The group order type. Valid values are: BRK, OCO, and NORMAL.
        :param orders: List of OrderRequest objects representing the orders in the group.
        :return: Response from the TradeStation API.
        """
        payload = {
            "Type": group_type,
            "Orders": [order.to_dict() for order in orders]
        }
        return await self._asend_request(method="POST", endpoint="orderexecution/ordergroupconfirm", payload=payload)

    def replace_order(self, order_id: str, quantity: Optional[str] = None, limit_price: Optional[str] = None,
                      stop_price: Optional[str] = None, order_type: Optional[Literal["Market"]] = None,
                      show_only_quantity: Optional[str] = None, trailing_stop: Optional[TrailingStop] = None,
                      market_activation_clear_all: Optional[bool] = None,
                      market_activation_rules: Optional[List[dict]] = None, time_activation_clear_all: Optional[bool] = None,
                      time_activation_rules: Optional[List[datetime]] = None):
        """
        Replaces an active order with a modified version of that order.

        :param order_id: The ID of the order to replace.
        :param quantity: The new quantity for the order.
        :param limit_price: The new limit price for the order.
        :param stop_price: The new stop price for the order.
        :param order_type: The new order type. Can only be updated to "Market".
        :param show_only_quantity: Hides the true number of shares intended to be bought or sold.
        :param trailing_stop: Trailing stop offset.
        :param market_activation_clear_all: If True, removes all market activation rules.
        :param market_activation_rules: List of market activation rules.
        :param time_activation_clear_all: If True, removes all time activation rules.
        :param time_activation_rules: List of datetime objects for time activation rules.
        :return: Response from the TradeStation API.
        """
        payload = {}
        if quantity:
            payload["Quantity"] = quantity
        if limit_price:
            payload["LimitPrice"] = limit_price
        if stop_price:
            payload["StopPrice"] = stop_price
        if order_type:
            payload["OrderType"] = order_type

        advanced_options = {}
        if show_only_quantity:
            advanced_options["ShowOnlyQuantity"] = show_only_quantity
        if trailing_stop:
            advanced_options["TrailingStop"] = trailing_stop.to_dict()
        if market_activation_clear_all is not None or market_activation_rules:
            advanced_options["MarketActivationRules"] = {}
            if market_activation_clear_all is not None:
                advanced_options["MarketActivationRules"]["ClearAll"] = market_activation_clear_all
            if market_activation_rules:
                advanced_options["MarketActivationRules"]["Rules"] = market_activation_rules
        if time_activation_clear_all is not None or time_activation_rules:
            advanced_options["TimeActivationRules"] = {}
            if time_activation_clear_all is not None:
                advanced_options["TimeActivationRules"]["ClearAll"] = time_activation_clear_all
            if time_activation_rules:
                advanced_options["TimeActivationRules"]["Rules"] = [
                    {"TimeUtc": rule.replace(microsecond=0).astimezone(timezone.utc).isoformat()} for rule in time_activation_rules
                ]

        if advanced_options:
            payload["AdvancedOptions"] = advanced_options

        return self._send_request(method="PUT", endpoint=f"orderexecution/orders/{order_id}", payload=payload)

    async def areplace_order(self, order_id: str, quantity: Optional[str] = None, limit_price: Optional[str] = None,
                             stop_price: Optional[str] = None, order_type: Optional[Literal["Market"]] = None,
                             show_only_quantity: Optional[str] = None, trailing_stop: Optional[TrailingStop] = None,
                             market_activation_clear_all: Optional[bool] = None,
                             market_activation_rules: Optional[List[dict]] = None, time_activation_clear_all: Optional[bool] = None,
                             time_activation_rules: Optional[List[datetime]] = None):
        """
        Asynchronously replaces an active order with a modified version of that order.

        :param order_id: The ID of the order to replace.
        :param quantity: The new quantity for the order.
        :param limit_price: The new limit price for the order.
        :param stop_price: The new stop price for the order.
        :param order_type: The new order type. Can only be updated to "Market".
        :param show_only_quantity: Hides the true number of shares intended to be bought or sold.
        :param trailing_stop: Trailing stop offset.
        :param market_activation_clear_all: If True, removes all market activation rules.
        :param market_activation_rules: List of market activation rules.
        :param time_activation_clear_all: If True, removes all time activation rules.
        :param time_activation_rules: List of datetime objects for time activation rules.
        :return: Response from the TradeStation API.
        """
        payload = {}
        if quantity:
            payload["Quantity"] = quantity
        if limit_price:
            payload["LimitPrice"] = limit_price
        if stop_price:
            payload["StopPrice"] = stop_price
        if order_type:
            payload["OrderType"] = order_type

        advanced_options = {}
        if show_only_quantity:
            advanced_options["ShowOnlyQuantity"] = show_only_quantity
        if trailing_stop:
            advanced_options["TrailingStop"] = trailing_stop.to_dict()
        if market_activation_clear_all is not None or market_activation_rules:
            advanced_options["MarketActivationRules"] = {}
            if market_activation_clear_all is not None:
                advanced_options["MarketActivationRules"]["ClearAll"] = market_activation_clear_all
            if market_activation_rules:
                advanced_options["MarketActivationRules"]["Rules"] = market_activation_rules
        if time_activation_clear_all is not None or time_activation_rules:
            advanced_options["TimeActivationRules"] = {}
            if time_activation_clear_all is not None:
                advanced_options["TimeActivationRules"]["ClearAll"] = time_activation_clear_all
            if time_activation_rules:
                advanced_options["TimeActivationRules"]["Rules"] = [
                    {"TimeUtc": rule.replace(microsecond=0).astimezone(timezone.utc).isoformat()} for rule in time_activation_rules
                ]

        if advanced_options:
            payload["AdvancedOptions"] = advanced_options

        return await self._asend_request(method="PUT", endpoint=f"orderexecution/orders/{order_id}", payload=payload)

    def get_activation_triggers(self):
        """
        Retrieves the available activation triggers with their corresponding keys.

        :return: Response from the TradeStation API.
        """
        return self._send_request(method="GET", endpoint="orderexecution/activationtriggers")

    async def aget_activation_triggers(self):
        """
        Asynchronously retrieves the available activation triggers with their corresponding keys.

        :return: Response from the TradeStation API.
        """
        return await self._asend_request(method="GET", endpoint="orderexecution/activationtriggers")

    def get_routes(self):
        """
        Retrieves a list of valid routes that a client can specify when posting an order.

        :return: Response from the TradeStation API.
        """
        return self._send_request(method="GET", endpoint="orderexecution/routes")

    async def aget_routes(self):
        """
        Asynchronously retrieves a list of valid routes that a client can specify when posting an order.

        :return: Response from the TradeStation API.
        """
        return await self._asend_request(method="GET", endpoint="orderexecution/routes")
