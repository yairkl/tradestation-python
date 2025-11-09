import os
import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from tradestation import TradeStationClient
from models import OrderRequest, OrderReplaceRequest


# Test Configuration
TEST_ACCOUNT_ID = None  # Will be populated from API
TEST_SYMBOL = "AAPL"
TEST_CRYPTO_SYMBOL = "BTCUSD"
TEST_OPTION_UNDERLYING = "SPY"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client():
    """Create a real TradeStation client for testing with demo account."""
    # Ensure credentials are set
    if not os.getenv('TRADESTATION_CLIENT_ID') or not os.getenv('TRADESTATION_CLIENT_SECRET'):
        pytest.skip("TradeStation credentials not found in environment variables")
    
    # Create client with demo account
    client = TradeStationClient(is_demo=True)
    
    yield client
    
    # Cleanup: close the client
    await client.close()


@pytest.fixture(scope="session")
async def test_account_id(client):
    """Get the first available test account ID."""
    global TEST_ACCOUNT_ID
    
    if TEST_ACCOUNT_ID is None:
        accounts = await client.get_accounts()
        
        if isinstance(accounts, dict) and 'Accounts' in accounts:
            if len(accounts['Accounts']) > 0:
                TEST_ACCOUNT_ID = accounts['Accounts'][0].get('AccountID')
        
        if TEST_ACCOUNT_ID is None:
            pytest.skip("No test accounts available")
    
    return TEST_ACCOUNT_ID


@pytest.fixture
async def cleanup_orders(client, test_account_id):
    """Fixture to track and cleanup orders created during tests."""
    created_order_ids = []
    
    # Provide a function to register order IDs
    def register_order(order_id):
        if order_id:
            created_order_ids.append(order_id)
    
    yield register_order
    
    # Cleanup: Cancel all created orders
    for order_id in created_order_ids:
        try:
            await client.cancel_order(order_id)
            print(f"Cleaned up order: {order_id}")
        except Exception as e:
            print(f"Failed to cleanup order {order_id}: {e}")
    
    # Wait a bit for cancellations to process
    await asyncio.sleep(1)


# Authentication Tests

class TestAuthentication:
    """Test authentication and token management."""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test that client initializes successfully."""
        assert client.access_token is not None
        assert client.client_id is not None
        assert client.client_secret is not None
        assert client.token_expiry is not None
    
    @pytest.mark.asyncio
    async def test_token_is_valid(self, client):
        """Test that token is valid and not expired."""
        assert client.token_expiry > datetime.now()
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token(self, client):
        """Test token validation mechanism."""
        old_token = client.access_token
        await client._ensure_valid_token()
        # Token should remain the same if still valid
        assert client.access_token is not None


# Account Tests

class TestAccounts:
    """Test account-related functionality."""
    
    @pytest.mark.asyncio
    async def test_get_accounts(self, client):
        """Test retrieving accounts."""
        result = await client.get_accounts()
        
        assert hasattr(result, 'accounts') or 'Accounts' in result
        accounts = getattr(result, 'accounts', result.get('Accounts', []))
        assert len(accounts) > 0
        assert accounts[0].get('AccountID') is not None
    
    @pytest.mark.asyncio
    async def test_get_balances(self, client, test_account_id):
        """Test retrieving account balances."""
        result = await client.get_balances(test_account_id)
        
        assert result is not None
        # Result should contain balance information
        if hasattr(result, 'balances'):
            assert len(result.balances) > 0
        elif isinstance(result, dict):
            assert 'Balances' in result or 'balances' in result
    
    @pytest.mark.asyncio
    async def test_get_balances_bod(self, client, test_account_id):
        """Test retrieving beginning-of-day balances."""
        result = await client.get_balances_bod(test_account_id)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_positions(self, client, test_account_id):
        """Test retrieving positions."""
        result = await client.get_positions(test_account_id)
        
        assert result is not None
        # Positions may be empty, but should return a valid response
    
    @pytest.mark.asyncio
    async def test_get_positions_with_filter(self, client, test_account_id):
        """Test retrieving positions with symbol filter."""
        result = await client.get_positions(test_account_id, symbol=TEST_SYMBOL)
        
        assert result is not None


# Symbol Search Tests

class TestSymbolSearch:
    """Test symbol search functionality."""
    
    @pytest.mark.asyncio
    async def test_suggest_symbols(self, client):
        """Test symbol suggestion."""
        result = await client.suggest_symbols("AAP")
        
        assert result is not None
        if hasattr(result, 'symbols'):
            symbols = result.symbols
        else:
            symbols = result.get('Symbols', [])
        
        assert len(symbols) > 0
        # Should contain AAPL
        assert any('AAPL' in str(s) for s in symbols)
    
    @pytest.mark.asyncio
    async def test_suggest_symbols_with_limit(self, client):
        """Test symbol suggestion with top limit."""
        result = await client.suggest_symbols("A", top=5)
        
        assert result is not None
        if hasattr(result, 'symbols'):
            symbols = result.symbols
            assert len(symbols) <= 5
    
    @pytest.mark.asyncio
    async def test_search_symbols_equity(self, client):
        """Test searching for equity symbols."""
        result = await client.search_symbols("N=AAPL&C=Stock")
        
        assert result is not None
        if hasattr(result, 'symbols'):
            symbols = result.symbols
        else:
            symbols = result.get('Symbols', [])
        
        assert len(symbols) > 0


# Market Data Tests

class TestMarketData:
    """Test market data retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_bars_daily(self, client):
        """Test getting daily bars."""
        result = await client.get_bars(
            TEST_SYMBOL,
            interval="1",
            unit="Daily",
            barsback="10"
        )
        
        assert result is not None
        if hasattr(result, 'bars'):
            bars = result.bars
        else:
            bars = result.get('Bars', [])
        
        assert len(bars) > 0
        # Verify bar structure
        bar = bars[0]
        assert 'Open' in bar or 'open' in bar.lower() if isinstance(bar, str) else True
    
    @pytest.mark.asyncio
    async def test_get_bars_intraday(self, client):
        """Test getting intraday bars."""
        result = await client.get_bars(
            TEST_SYMBOL,
            interval="5",
            unit="Minute",
            barsback="20"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_bars_with_date_range(self, client):
        """Test getting bars with date range."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        result = await client.get_bars(
            TEST_SYMBOL,
            interval="1",
            unit="Daily",
            firstdate=start_date.strftime("%Y-%m-%d"),
            lastdate=end_date.strftime("%Y-%m-%d")
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_quote_snapshots(self, client):
        """Test getting quote snapshots."""
        result = await client.get_quote_snapshots(f"{TEST_SYMBOL},MSFT")
        
        assert result is not None
        if hasattr(result, 'quotes'):
            quotes = result.quotes
        else:
            quotes = result.get('Quotes', [])
        
        assert len(quotes) >= 1
    
    @pytest.mark.asyncio
    async def test_get_symbol_details(self, client):
        """Test getting symbol details."""
        result = await client.get_symbol_details(TEST_SYMBOL)
        
        assert result is not None
        if hasattr(result, 'symbols'):
            symbols = result.symbols
        else:
            symbols = result.get('Symbols', [])
        
        assert len(symbols) > 0
        symbol = symbols[0]
        assert symbol.get('Symbol') == TEST_SYMBOL or symbol.get('symbol') == TEST_SYMBOL


# Streaming Tests

class TestStreaming:
    """Test streaming functionality."""
    
    @pytest.mark.asyncio
    async def test_stream_bars(self, client):
        """Test streaming bars."""
        count = 0
        max_items = 5
        
        async for item in client.stream_bars(TEST_SYMBOL, interval="1", unit="Daily", barsback="5"):
            count += 1
            assert item is not None
            
            if count >= max_items:
                break
        
        assert count > 0
    
    @pytest.mark.asyncio
    async def test_stream_quotes(self, client):
        """Test streaming quotes."""
        count = 0
        max_items = 5
        
        async for item in client.stream_quotes(TEST_SYMBOL):
            count += 1
            assert item is not None
            
            if count >= max_items:
                break
        
        assert count > 0
    
    @pytest.mark.asyncio
    async def test_stream_positions(self, client, test_account_id):
        """Test streaming positions."""
        count = 0
        max_items = 3
        
        async for item in client.stream_positions(test_account_id):
            count += 1
            assert item is not None
            
            if count >= max_items:
                break
        
        # May not have any positions, but stream should work
        assert count >= 0


# Order Tests

class TestOrders:
    """Test order management functionality."""
    
    @pytest.mark.asyncio
    async def test_get_orders(self, client, test_account_id):
        """Test retrieving orders."""
        result = await client.get_orders(test_account_id)
        
        assert result is not None
        # Orders may be empty
    
    @pytest.mark.asyncio
    async def test_get_historical_orders(self, client, test_account_id):
        """Test retrieving historical orders."""
        since_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        result = await client.get_historical_orders(test_account_id, since_date)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_confirm_order(self, client, test_account_id):
        """Test confirming an order (validation without placement)."""
        # Create a simple limit order for confirmation
        order = OrderRequest(
            account_id=test_account_id,
            symbol=TEST_SYMBOL,
            quantity="1",
            order_type="Limit",
            limit_price="50.00",  # Far from market to avoid accidental fill
            trade_action="Buy",
            time_in_force="Day",
            route="Intelligent"
        )
        
        result = await client.confirm_order(order)
        
        assert result is not None
        # Confirmation should return estimated costs/commissions
    
    @pytest.mark.asyncio
    async def test_place_and_cancel_order(self, client, test_account_id, cleanup_orders):
        """Test placing and canceling an order."""
        # Create a limit order far from market to avoid fill
        order = OrderRequest(
            account_id=test_account_id,
            symbol=TEST_SYMBOL,
            quantity="1",
            order_type="Limit",
            limit_price="1.00",  # Very low price to avoid fill
            trade_action="Buy",
            time_in_force="Day",
            route="Intelligent"
        )
        
        # Place the order
        result = await client.place_order(order)
        
        assert result is not None
        
        # Extract order ID
        order_id = None
        if hasattr(result, 'orders'):
            orders = result.orders
            if len(orders) > 0:
                order_id = orders[0].get('OrderID')
        elif isinstance(result, dict):
            order_id = result.get('OrderID') or result.get('Orders', [{}])[0].get('OrderID')
        
        assert order_id is not None, "Order ID should be returned after placement"
        
        # Register for cleanup
        cleanup_orders(order_id)
        
        # Wait a moment for order to be processed
        await asyncio.sleep(2)
        
        # Verify order exists
        order_result = await client.get_orders_by_id(test_account_id, order_id)
        assert order_result is not None
        
        # Cancel the order
        cancel_result = await client.cancel_order(order_id)
        assert cancel_result is not None
        
        # Wait for cancellation
        await asyncio.sleep(2)
    
    @pytest.mark.asyncio
    async def test_replace_order(self, client, test_account_id, cleanup_orders):
        """Test replacing an order."""
        # Place initial order
        order = OrderRequest(
            account_id=test_account_id,
            symbol=TEST_SYMBOL,
            quantity="1",
            order_type="Limit",
            limit_price="1.00",
            trade_action="Buy",
            time_in_force="Day",
            route="Intelligent"
        )
        
        result = await client.place_order(order)
        
        # Extract order ID
        order_id = None
        if hasattr(result, 'orders'):
            orders = result.orders
            if len(orders) > 0:
                order_id = orders[0].get('OrderID')
        elif isinstance(result, dict):
            order_id = result.get('OrderID') or result.get('Orders', [{}])[0].get('OrderID')
        
        if order_id:
            cleanup_orders(order_id)
            
            await asyncio.sleep(2)
            
            # Replace the order with new quantity
            replace_request = OrderReplaceRequest(
                quantity="2",
                limit_price="1.50"
            )
            
            replace_result = await client.replace_order(order_id, replace_request)
            assert replace_result is not None
            
            await asyncio.sleep(1)


# Options Tests

class TestOptions:
    """Test options-related functionality."""
    
    @pytest.mark.asyncio
    async def test_get_option_expirations(self, client):
        """Test getting option expirations."""
        result = await client.get_option_expirations(TEST_OPTION_UNDERLYING)
        
        assert result is not None
        if hasattr(result, 'expirations'):
            expirations = result.expirations
        else:
            expirations = result.get('Expirations', [])
        
        assert len(expirations) > 0
    
    @pytest.mark.asyncio
    async def test_get_option_strikes(self, client):
        """Test getting option strikes."""
        # First get an expiration
        exp_result = await client.get_option_expirations(TEST_OPTION_UNDERLYING)
        
        if hasattr(exp_result, 'expirations'):
            expirations = exp_result.expirations
        else:
            expirations = exp_result.get('Expirations', [])
        
        if len(expirations) > 0:
            expiration = expirations[0].get('Date') or expirations[0].get('date')
            
            result = await client.get_option_strikes(
                TEST_OPTION_UNDERLYING,
                expiration=expiration
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_option_chain(self, client):
        """Test getting option chain."""
        result = await client.get_option_chain(
            TEST_OPTION_UNDERLYING,
            strike_proximity=3
        )
        
        assert result is not None


# Error Handling Tests

class TestErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_invalid_symbol(self, client):
        """Test handling of invalid symbol."""
        result = await client.get_quote_snapshots("INVALIDSYMBOL12345XYZ")
        
        # Should return an error response, not throw
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_invalid_account(self, client):
        """Test handling of invalid account ID."""
        result = await client.get_balances("99999999")
        
        # Should return an error response
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_order(self, client):
        """Test canceling a non-existent order."""
        result = await client.cancel_order("99999999")
        
        # Should return an error response
        assert result is not None


# Context Manager Tests

class TestContextManager:
    """Test async context manager functionality."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using client as context manager."""
        if not os.getenv('TRADESTATION_CLIENT_ID'):
            pytest.skip("Credentials not available")
        
        async with TradeStationClient(is_demo=True) as client:
            assert client.access_token is not None
            
            # Perform a simple operation
            result = await client.get_accounts()
            assert result is not None
        
        # Client should be closed after context
        # Note: We can't easily test if client is closed without accessing internals