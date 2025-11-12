import asyncio
from tradestation import TradeStationClient
from tradestation.models import Bar


async def main():
    # Initialize client (uses env vars for credentials)
    async with TradeStationClient(is_demo=True) as client:
        ema = None
        alpha = 0.1
        # Stream market data for a symbol in 5-minute bars interval
        async for market_data in client.stream_bars(symbol="AAPL", interval="1", unit="Minute"):
            # Process incoming market data. can be Bar, Heartbeat, or StreamErrorResponse
            if isinstance(market_data, Bar):
                
                # Update EMA on bar close
                if market_data.bar_status == "Closed":
                    if ema is None:
                        ema = market_data.close
                    # Calculate EMA
                    ema = alpha * market_data.close + (1 - alpha) * ema
                    
                print(f"AAPL Last Price: ${market_data.close}, EMA: ${ema:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
