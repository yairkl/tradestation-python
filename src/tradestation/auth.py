from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode, urlparse, parse_qs
import threading
from .exceptions import AuthenticationError
from datetime import datetime, timedelta
import webbrowser
import os
from typing import Optional
import httpx

AUTH_URL = "https://signin.tradestation.com/authorize"
TOKEN_URL = "https://signin.tradestation.com/oauth/token"

AUTH_SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authentication Successful</title>
    <script>
        setTimeout(() => window.close(), 1000);
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
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_GET(self):
        """Handle GET request with OAuth code."""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        if 'code' not in query_params:
            self.send_error(400, "Error: No authorization code received")
            return

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(AUTH_SUCCESS_HTML.encode('utf-8'))
        
        # Exchange code for token
        code = query_params['code'][0]
        self.server.auth_instance._exchange_code_for_token(code)
        
        # Stop the server in a separate thread
        threading.Thread(target=self.server.shutdown, daemon=True).start()

class AuthManager:
    """Manages OAuth authentication and token refresh."""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        port: int = 31022,
        refresh_token_margin: float = 60
    ):
        self.client_id = client_id or os.getenv('TRADESTATION_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('TRADESTATION_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise AuthenticationError(
                "client_id and client_secret must be provided"
            )
        
        self.port = port
        self.redirect_uri = f'http://localhost:{port}/'
        self.refresh_margin = timedelta(seconds=refresh_token_margin)
        
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        
        self._authenticate()
    
    def _authenticate(self):
        """Perform OAuth authentication flow."""
        # Implementation from previous code
        self._start_server()
        auth_url = self._generate_auth_url()
        
        print(f"Opening browser for authentication...")
        webbrowser.open(auth_url)
        
        # Wait for authentication to complete
        while self.access_token is None:
            pass
        
    def _start_server(self):
        """Start a local HTTP server to handle OAuth callback."""
        server = HTTPServer(("127.0.0.1", self.port), OAuthHandler)
        server.auth_instance = self
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server

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

    async def ensure_valid_token(self):
        """Ensure token is valid, refresh if needed."""
        if self.token_expiry and datetime.now() >= (self.token_expiry - self.refresh_margin):
            await self.refresh_access_token()
    
    async def refresh_access_token(self):
        """Refresh the access token."""
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
    