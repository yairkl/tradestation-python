import asyncio
from tradestation import TradeStationClient
from tradestation.models import ErrorResponse

async def main():
    # Initialize client (uses env vars for credentials)
    async with TradeStationClient(is_demo=True) as client:
        # Get all accounts
        accounts = await client.get_accounts()
        print(f"Found {len(accounts)} accounts")
        account_ids = ','.join([account.account_id for account in accounts])
        
        # Get account balances
        balances = await client.get_balances(account_ids)
        if isinstance(balances, ErrorResponse):
            print(f"Error fetching balances: {balances}")
            return
        for balance in balances.balances:
            print(f"Account {balance.account_id},  Cash Balance: ${balance.cash_balance}, Total Equity: ${balance.equity}")
            
        # Get positions
        positions = await client.get_positions(account_ids)
        for position in positions.positions:
            print(f"{position.symbol}: {position.quantity} shares market value ${position.market_value}")


if __name__ == "__main__":
    asyncio.run(main())
