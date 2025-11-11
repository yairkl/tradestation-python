import json
import os
import threading
import webbrowser
from datetime import datetime, timedelta
from typing import AsyncGenerator, Optional, Union, List
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode, urlparse, parse_qs
import httpx
from pydantic import TypeAdapter

from .models import *
from .auth import OAuthHandler

# API Configuration
AUTH_URL = "https://signin.tradestation.com/authorize"
TOKEN_URL = "https://signin.tradestation.com/oauth/token"
LIVE_API_URL = "https://api.tradestation.com"
DEMO_API_URL = "https://sim-api.tradestation.com"

class TradeStationClient:
    """Client for interacting with the TradeStation API."""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        port: int = 31022,
        is_demo: bool = True,
        refresh_token_margin: float = 60
    ):
        """
        Initialize TradeStation client.
        
        Args:
            client_id: OAuth client ID (or set TRADESTATION_CLIENT_ID env var)
            client_secret: OAuth client secret (or set TRADESTATION_CLIENT_SECRET env var)
            port: Local port for OAuth callback
            is_demo: Use demo API if True, live API if False
            refresh_token_margin: Seconds before token expiry to refresh
        """
        self.client_id = client_id or os.getenv('TRADESTATION_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('TRADESTATION_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "client_id and client_secret must be provided either as arguments "
                "or through TRADESTATION_CLIENT_ID and TRADESTATION_CLIENT_SECRET environment variables"
            )
        
        self.port = port
        self.base_url = DEMO_API_URL if is_demo else LIVE_API_URL
        self.redirect_uri = f'http://localhost:{self.port}/'
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.refresh_margin = timedelta(seconds=refresh_token_margin)
        
        # Authenticate and create HTTP client
        self._authenticate()
        self.client = httpx.AsyncClient(
            headers={'Authorization': f'Bearer {self.access_token}'},
            timeout=30.0
        )
    
    def _generate_auth_url(self) -> str:
        """Generate the authentication URL for TradeStation OAuth."""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'audience': 'https://api.tradestation.com',
            'redirect_uri': self.redirect_uri,
            'scope': 'openid profile offline_access MarketData ReadAccount Trade',
            'state': 'xyzv'
        }
        return f"{AUTH_URL}?{urlencode(params)}"
    
    def _start_server(self):
        """Start a local HTTP server to handle OAuth callback."""
        server = HTTPServer(("127.0.0.1", self.port), OAuthHandler)
        server.auth_instance = self
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server
    
    def _authenticate(self):
        """Handle the authentication flow."""
        self._start_server()
        auth_url = self._generate_auth_url()
        
        print(f"Opening browser for authentication...")
        webbrowser.open(auth_url)
        
        # Wait for authentication to complete
        while self.access_token is None:
            pass
        
        print("Authentication successful!")
    
    def _exchange_code_for_token(self, code: str):
        """Exchange authorization code for an access token."""
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
            response.raise_for_status()
            
            body = response.json()
            self.access_token = body['access_token']
            self.refresh_token = body.get('refresh_token')
            self.token_expiry = datetime.now() + timedelta(seconds=body.get('expires_in', 1200))
    
    async def _ensure_valid_token(self):
        """Ensure the access token is valid, refresh if necessary."""
        if self.token_expiry and datetime.now() >= (self.token_expiry - self.refresh_margin):
            await self._refresh_access_token()
    
    async def _refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(TOKEN_URL, data=data, headers=headers)
            response.raise_for_status()
            
            body = response.json()
            self.access_token = body['access_token']
            self.token_expiry = datetime.now() + timedelta(seconds=body.get('expires_in', 1200))
            
            # Update client headers
            self.client.headers.update({'Authorization': f'Bearer {self.access_token}'})
    
    async def close(self):
        """Close the HTTP client."""
        print("Closing TradeStation client...")
        try:
            await self.client.aclose()
        except RuntimeError as e:
            if "Event loop is closed" not in str(e):
                raise
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    # Symbol Search Methods
    
    async def suggest_symbols(
        self,
        text: str,
        top: Optional[int] = None,
        filter_expr: Optional[str] = None
    ) -> Union[Error, List[SymbolSuggestDefinition]]:
        """
        Suggest symbols based on partial input.
        
        Args:
            text: Partial symbol name, company name, or description
            top: Maximum number of results to return
            filter_expr: OData filter expression (e.g., "Category eq 'Stock'")
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v2/data/symbols/suggest/{text}"
        params = {}
        if top is not None:
            params['$top'] = top
        if filter_expr is not None:
            params['$filter'] = filter_expr
        
        response = await self.client.get(url, params=params)
        
        if response.status_code == 200:
            return SymbolSuggestDefinitions.model_validate(response.json()).root
        else:
            return Error.from_dict(response.json())
    
    async def search_symbols(self, criteria: str) -> Union[Error, List[SymbolSearchDefinition]]:
        """
        Search for symbols using detailed criteria.
        
        Args:
            criteria: Search criteria as key/value pairs (e.g., "N=MSFT&C=Stock")
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v2/data/symbols/search/{criteria}"
        response = await self.client.get(url)
        
        if response.status_code == 200:
            return SymbolSearchDefinitions.model_validate(response.json()).root
        else:
            return Error.from_dict(response.json())
    
    # Account Methods
    
    async def get_accounts(self) -> Union[Accounts, ErrorResponse]:
        """Get all accounts for the authenticated user."""
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/brokerage/accounts"
        response = await self.client.get(url)
        
        if response.status_code == 200:
            return Accounts.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def get_balances(self, accounts: str) -> Union[Balances, ErrorResponse]:
        """
        Get account balances.
        
        Args:
            accounts: Comma-separated account IDs (e.g., "123456,789012")
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/balances"
        response = await self.client.get(url)
        
        if response.status_code == 200:
            return Balances.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def get_balances_bod(self, accounts: str) -> Union[BalancesBOD, ErrorResponse]:
        """
        Get beginning-of-day account balances.
        
        Args:
            accounts: Comma-separated account IDs
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/bodbalances"
        response = await self.client.get(url)
        
        if response.status_code == 200:
            return BalancesBOD.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def get_positions(
        self,
        accounts: str,
        symbol: Optional[str] = None
    ) -> Union[ErrorResponse, Positions]:
        """
        Get positions for accounts.
        
        Args:
            accounts: Comma-separated account IDs
            symbol: Optional symbol filter (supports wildcards, e.g., "MSFT *")
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/positions"
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        response = await self.client.get(url, params=params)
        
        if response.status_code == 200:
            return Positions.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    # Order Methods
    
    async def get_orders(
        self,
        accounts: str,
        page_size: Optional[int] = None,
        next_token: Optional[str] = None
    ) -> Union[ErrorResponse, Orders]:
        """
        Get orders for accounts.
        
        Args:
            accounts: Comma-separated account IDs
            page_size: Number of orders per page (max 600)
            next_token: Pagination token from previous response
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/orders"
        params = {}
        if page_size:
            params['pageSize'] = page_size
        if next_token:
            params['nextToken'] = next_token
        
        response = await self.client.get(url, params=params)
        
        if response.status_code == 200:
            return Orders.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def get_orders_by_id(
        self,
        accounts: str,
        order_ids: str
    ) -> Union[ErrorResponse, OrdersById]:
        """
        Get specific orders by ID.
        
        Args:
            accounts: Comma-separated account IDs
            order_ids: Comma-separated order IDs
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/orders/{order_ids}"
        response = await self.client.get(url)
        
        if response.status_code == 200:
            return OrdersById.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def get_historical_orders(
        self,
        accounts: str,
        since: str,
        page_size: Optional[int] = None,
        next_token: Optional[str] = None
    ) -> Union[ErrorResponse, HistoricalOrders]:
        """
        Get historical orders.
        
        Args:
            accounts: Comma-separated account IDs
            since: Date in format "YYYY-MM-DD" (max 90 days back)
            page_size: Number of orders per page (max 600)
            next_token: Pagination token
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/brokerage/accounts/{accounts}/historicalorders"
        params = {'since': since}
        if page_size:
            params['pageSize'] = page_size
        if next_token:
            params['nextToken'] = next_token
        
        response = await self.client.get(url, params=params)
        
        if response.status_code == 200:
            return HistoricalOrders.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def place_order(self, order: OrderRequest) -> Union[ErrorResponse, OrderResponses]:
        """
        Place a new order.
        
        Args:
            order: Order request object
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/orderexecution/orders"
        
        response = await self.client.post(
            url,
            json=order.to_dict(),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return OrderResponses.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def confirm_order(self, order: OrderRequest) -> Union[ErrorResponse, List[OrderConfirmResponse]]:
        """
        Confirm order details without placing it.
        
        Args:
            order: Order request object
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/orderexecution/orderconfirm"
        response = await self.client.post(url, json=order.to_dict())
        
        if response.status_code == 200:
            return OrderConfirmResponses.model_validate(response.json()).confirmations
            # return [OrderConfirmResponse.from_dict(item) for item in response.json()]
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def replace_order(
        self,
        order_id: str,
        order: OrderReplaceRequest
    ) -> Union[ErrorResponse, OrderResponse]:
        """
        Replace an existing order.
        
        Args:
            order_id: Order ID to replace
            order: Replacement order details
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/orderexecution/orders/{order_id}"
        response = await self.client.put(url, json=order.to_dict())
        
        if response.status_code == 200:
            return OrderResponse.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def cancel_order(self, order_id: str) -> Union[ErrorResponse, OrderResponse]:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/orderexecution/orders/{order_id}"
        response = await self.client.delete(url)
        
        if response.status_code == 200:
            return OrderResponse.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    # Market Data Methods
    
    async def get_bars(
        self,
        symbol: str,
        interval: Optional[str] = "1",
        unit: Optional[str] = "Daily",
        barsback: Optional[str] = None,
        firstdate: Optional[str] = None,
        lastdate: Optional[str] = None,
        sessiontemplate: Optional[str] = None
    ) -> Union[Bars, ErrorResponse]:
        """
        Get historical bar data.
        
        Args:
            symbol: Valid symbol string
            interval: Bar interval (e.g., "1" for 1-minute bars)
            unit: Time unit (Minute, Daily, Weekly, Monthly)
            barsback: Number of bars to retrieve
            firstdate: Start date (YYYY-MM-DD)
            lastdate: End date (YYYY-MM-DD)
            sessiontemplate: Session template for extended hours
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/marketdata/barcharts/{symbol}"
        params = {}
        
        if interval:
            params['interval'] = interval
        if unit:
            params['unit'] = unit
        if barsback:
            params['barsback'] = barsback
        if firstdate:
            params['firstdate'] = firstdate
        if lastdate:
            params['lastdate'] = lastdate
        if sessiontemplate:
            params['sessiontemplate'] = sessiontemplate
        
        response = await self.client.get(url, params=params)
        
        if response.status_code == 200:
            return Bars.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def stream_bars(
        self,
        symbol: str,
        interval: str = "1",
        unit: str = "Daily",
        barsback: Optional[str] = None,
        sessiontemplate: Optional[str] = None
    ) -> AsyncGenerator[Union[Bar, Heartbeat, StreamErrorResponse], None]:
        """
        Stream real-time bar data.
        
        Args:
            symbol: Valid symbol string
            interval: Bar interval
            unit: Time unit
            barsback: Number of historical bars
            sessiontemplate: Session template
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/marketdata/stream/barcharts/{symbol}"
        params = {'interval': interval, 'unit': unit}
        
        if barsback:
            params['barsback'] = barsback
        if sessiontemplate:
            params['sessiontemplate'] = sessiontemplate
        
        async with self.client.stream('GET', url, params=params) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line or not line.strip():
                    continue
                
                try:
                    obj = json.loads(line)
                    yield TypeAdapter(Union[Bar, Heartbeat, StreamErrorResponse]).validate_python(obj)
                except Exception as e:
                    print(f"Error parsing line: {e}")
                    continue
    
    async def get_quote_snapshots(self, symbols: str) -> Union[ErrorResponse, QuoteSnapshot]:
        """
        Get quote snapshots for symbols.
        
        Args:
            symbols: Comma-separated symbols (max 100)
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/marketdata/quotes/{symbols}"
        response = await self.client.get(url)
        
        if response.status_code == 200:
            return QuoteSnapshot.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def stream_quotes(
        self,
        symbols: str
    ) -> AsyncGenerator[Union[Heartbeat, QuoteStream, StreamErrorResponse], None]:
        """
        Stream real-time quotes.
        
        Args:
            symbols: Comma-separated symbols (max 100)
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/marketdata/stream/quotes/{symbols}"
        
        async with self.client.stream('GET', url) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line or not line.strip():
                    continue
                
                try:
                    obj = json.loads(line)
                    yield TypeAdapter(Union[Heartbeat, QuoteStream, StreamErrorResponse]).validate_python(obj)
                except Exception as e:
                    print(f"Error parsing line: {e}")
                    continue
    
    async def get_symbol_details(self, symbols: str) -> Union[ErrorResponse, SymbolDetailsResponse]:
        """
        Get detailed symbol information.
        
        Args:
            symbols: Comma-separated symbols (max 50)
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/marketdata/symbols/{symbols}"
        response = await self.client.get(url)
        
        if response.status_code == 200:
            return SymbolDetailsResponse.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    # Options Methods
    
    async def get_option_expirations(
        self,
        underlying: str,
        strike_price: Optional[float] = None
    ) -> Union[ErrorResponse, Expirations]:
        """
        Get option expiration dates.
        
        Args:
            underlying: Underlying symbol
            strike_price: Optional strike price filter
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/marketdata/options/expirations/{underlying}"
        params = {}
        if strike_price is not None:
            params['strikePrice'] = strike_price
        
        response = await self.client.get(url, params=params)
        
        if response.status_code == 200:
            return Expirations.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def get_option_strikes(
        self,
        underlying: str,
        spread_type: str = "Single",
        strike_interval: int = 1,
        expiration: Optional[str] = None,
        expiration2: Optional[str] = None
    ) -> Union[ErrorResponse, Strikes]:
        """
        Get option strike prices.
        
        Args:
            underlying: Underlying symbol
            spread_type: Spread type name
            strike_interval: Interval between strikes
            expiration: First expiration date
            expiration2: Second expiration (for spreads)
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/marketdata/options/strikes/{underlying}"
        params = {
            'spreadType': spread_type,
            'strikeInterval': strike_interval
        }
        
        if expiration:
            params['expiration'] = expiration
        if expiration2:
            params['expiration2'] = expiration2
        
        response = await self.client.get(url, params=params)
        
        if response.status_code == 200:
            return Strikes.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    async def get_option_chain(
        self,
        underlying: str,
        expiration: Optional[str] = None,
        strike_proximity: int = 5,
        spread_type: str = "Single",
        enable_greeks: bool = True,
        option_type: str = "All"
    ) -> Union[ErrorResponse, Spread]:
        """
        Get option chain data.
        
        Args:
            underlying: Underlying symbol
            expiration: Expiration date
            strike_proximity: Number of strikes above/below center
            spread_type: Spread type
            enable_greeks: Include Greeks in response
            option_type: Filter by Call, Put, or All
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/marketdata/stream/options/chains/{underlying}"
        params = {
            'strikeProximity': strike_proximity,
            'spreadType': spread_type,
            'enableGreeks': enable_greeks,
            'optionType': option_type
        }
        
        if expiration:
            params['expiration'] = expiration
        
        response = await self.client.get(url, params=params)
        
        if response.status_code == 200:
            return Spread.from_dict(response.json())
        else:
            return ErrorResponse.from_dict(response.json())
    
    # Streaming Methods
    
    async def stream_orders(
        self,
        accounts: str
    ) -> AsyncGenerator[Union[Heartbeat, Order, StreamOrderErrorResponse, StreamStatus], None]:
        """
        Stream order updates.
        
        Args:
            accounts: Comma-separated account IDs
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/brokerage/stream/accounts/{accounts}/orders"
        
        async with self.client.stream('GET', url) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line or not line.strip():
                    continue
                
                try:
                    obj = json.loads(line)
                    yield TypeAdapter(Union[Order, Heartbeat, StreamOrderErrorResponse, StreamStatus]).validate_python(obj)
                except Exception as e:
                    print(f"Error parsing line: {e}")
                    continue
    
    async def stream_positions(
        self,
        accounts: str,
        changes: bool = False
    ) -> AsyncGenerator[Union[Heartbeat, Position, StreamPositionsErrorResponse, StreamStatus], None]:
        """
        Stream position updates.
        
        Args:
            accounts: Comma-separated account IDs
            changes: Stream only changes (after initial snapshot)
        """
        await self._ensure_valid_token()
        url = f"{self.base_url}/v3/brokerage/stream/accounts/{accounts}/positions"
        params = {'changes': changes}
        
        async with self.client.stream('GET', url, params=params) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line or not line.strip():
                    continue
                
                try:
                    obj = json.loads(line)
                    yield TypeAdapter(Union[Heartbeat, Position, StreamPositionsErrorResponse, StreamStatus]).validate_python(obj)
                except Exception as e:
                    print(f"Error parsing line: {e}")
                    continue