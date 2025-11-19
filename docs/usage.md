# Usage

This project provides an async-first client for TradeStation: `TradeStationClient`.
The client is used via an async context manager and exposes async methods for
market data, account/brokerage operations, orders, and streaming.
---

## Initialization

The client is asynchronous and expects OAuth credentials. Provide credentials
either via constructor arguments or environment variables:

- `TRADESTATION_CLIENT_ID`
- `TRADESTATION_CLIENT_SECRET`

Create the client with the `is_demo` flag to choose the demo vs live API.

```python
from tradestation import TradeStationClient

# Preferred: async context manager usage
async with TradeStationClient(is_demo=True) as client:
    # use `client` inside this block
    pass

# Or create and close manually (not recommended unless necessary)
client = TradeStationClient(is_demo=True, client_id="...", client_secret="...")
await client.close()
```

Note: the client opens a browser window to complete the OAuth flow during
initialization if tokens are not already available. See `src/tradestation/client.py`
for details.

---

## Authentication

Authentication is handled inside `TradeStationClient`. On initialization the
client starts an OAuth flow which will open your browser and prompt for
authorization. Tokens are stored in-memory for the lifetime of the client.

You typically do not need to call any auth methods directly; just instantiate
the client as shown above.

---

## Market Data

### Fetch historical bars

Use `get_bars` to request historical bar data.

```python
from tradestation import TradeStationClient

async def fetch_bars():
    async with TradeStationClient(is_demo=True) as client:
        bars = await client.get_bars(symbol="AAPL", interval="1", unit="Minute", barsback="10")
        for b in bars:
            print(b.time, b.open, b.high, b.low, b.close)

```

### Stream bars (real-time)

Use `stream_bars` to receive an async generator of bar objects and heartbeats.

```python
async with TradeStationClient(is_demo=True) as client:
    async for event in client.stream_bars(symbol="AAPL", interval="1", unit="Minute"):
        # event may be a Bar, Heartbeat, or a StreamErrorResponse
        print(event)

```

### Quotes and symbol details

Use `get_quote_snapshots`, `stream_quotes`, and `get_symbol_details` for
quotes and symbol metadata.

---

## Accounts & Positions

### Get accounts

```python
async with TradeStationClient(is_demo=True) as client:
    accounts = await client.get_accounts()
    for a in accounts:
        print(a.account_id, a.account_type)

```

### Get balances and positions

Balances and positions APIs accept a comma-separated string of account ids.

```python
async with TradeStationClient(is_demo=True) as client:
    balances = await client.get_balances("12345,67890")
    positions = await client.get_positions("12345,67890", symbol=None)
    print(balances, positions)

```

---

## Order Management

The client exposes several order endpoints. The primary method for placing
orders is `place_order`, which accepts an `OrderRequest` model from
`tradestation.models`.

### Place an order

```python
from tradestation import TradeStationClient
from tradestation.models import OrderRequest, TradeAction, TimeInForceRequest, Duration, OrderType

async def place_order_example():
    async with TradeStationClient(is_demo=True) as client:
        accounts = await client.get_accounts()
        account_id = accounts[0].account_id

        order = OrderRequest(
            account_id=account_id,
            symbol="AAPL",
            quantity="10",
            order_type=OrderType.MARKET,
            trade_action=TradeAction.BUY,
            time_in_force=TimeInForceRequest(duration=Duration.GTC),
        )

        resp = await client.place_order(order)
        print(resp)

```

`place_order` returns either an `OrderResponses` object or an `ErrorResponse`.

### Confirm / Replace / Cancel

- `confirm_order(order: OrderRequest)` — returns estimated costs/commissions without placing the order.
- `replace_order(order_id: str, order: OrderReplaceRequest)` — replace an existing order.
- `cancel_order(order_id: str)` — cancel an order.

All of these are async and return either success response models or `ErrorResponse`.

### Streaming order updates

Use `stream_orders` with a comma-separated list of account IDs to receive an
async stream of `Order` objects and status updates.

```python
async with TradeStationClient(is_demo=True) as client:
    async for event in client.stream_orders("12345"):
        # event may be Order, Heartbeat, StreamOrderErrorResponse, or StreamStatus
        print(event)

```

When listening for order updates, track order IDs and inspect the `status`
field to detect terminal states (e.g., Filled, Cancelled, Rejected, Expired,
or Out). The example scripts in `examples/` demonstrate a practical pattern for
tracking multiple orders and exiting once they are all terminal.

---

## Other features

- Symbol search: `suggest_symbols(text, top=None, filter_expr=None)` and
  `search_symbols(criteria)`.
- Options endpoints: `get_option_expirations`, `get_option_strikes`,
  `get_option_chain`.
- Quote snapshots and streaming: `get_quote_snapshots`, `stream_quotes`.

Refer to the client source (`src/tradestation/client.py`) for full details and
available model types in `src/tradestation/models.py`.

---

## Notes

- This client is async-first; there are no synchronous `get_`/`place_` wrappers in
  the current implementation. Use `asyncio.run(...)` or an existing event loop to
  drive the API calls.
- All network calls will raise or return `ErrorResponse` objects on failure;
  check responses accordingly.

## Conclusion

The `TradeStationClient` provides a modern async interface to TradeStation's
market data and brokerage APIs. Use the examples in the `examples/` directory
(`place_order.py`, `place_order_advanced.py`, etc.) as practical templates for
common tasks like placing orders and streaming updates.