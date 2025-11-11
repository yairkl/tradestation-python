# TradeStation Python Client

A comprehensive Python library for interacting with the TradeStation API.

## Features

- 🔐 OAuth 2.0 authentication with automatic token refresh
- 📊 Real-time market data streaming
- 💼 Account management (balances, positions, orders)
- 📈 Historical and real-time bar data
- 🎯 Options chain and analytics
- ⚡ Async/await support
- 🛡️ Type hints and comprehensive error handling

## Installation

```bash
pip install tradestation-python
```

## Quick Start

```python
import asyncio
from tradestation import TradeStationClient

async def main():
    async with TradeStationClient(is_demo=True) as client:
        # Get accounts
        accounts = await client.accounts.get_all()
        
        # Get quote
        quote = await client.market_data.get_quotes("AAPL")
        
        # Stream real-time quotes
        async for quote_update in client.stream.quotes("AAPL"):
            print(quote_update)

asyncio.run(main())
```

## Documentation

Full documentation available at: [Docs](docs/index.md)

## Authentication

Set environment variables:

```bash
export TRADESTATION_CLIENT_ID="your_client_id"
export TRADESTATION_CLIENT_SECRET="your_client_secret"
```

Or pass directly:

```python
client = TradeStationClient(
    client_id="your_client_id",
    client_secret="your_client_secret"
)
```

## Examples

See the [Examples](examples/) directory for more usage examples.

## Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## License

MIT License - see LICENSE file for details.
