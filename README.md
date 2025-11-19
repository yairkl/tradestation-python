# TradeStation Python Client
> Disclamer: this library is unofficial and not maintained by tradestation. use at your own risk

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

install from GitHub repository:
```bash
pip install git+https://github.com/yairkl/tradestation-python.git
```

install from source:
```bash
git clone https://github.com/yairkl/tradestation-python.git
cd tradestation-python
pip install .
```

## Quick Start

```python
import asyncio
from tradestation import TradeStationClient

async def main():
    async with TradeStationClient(
        client_id=<your_client_id>,
        client_secret=<your_client_secret>,
        is_demo=True
    ) as client:
        # Get accounts
        accounts = await client.get_accounts()
        
        # Get quote
        quote = await client.get_bars("AAPL")
        
        # Stream real-time quotes
        async for quote_update in client.stream_bars("AAPL"):
            print(quote_update)

asyncio.run(main())
```

## Documentation

Full documentation available at: [Docs](docs/index.md)

Official TradeStation API specification is available at: [Specification](https://api.tradestation.com/docs/specification)

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
