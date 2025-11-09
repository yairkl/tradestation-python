import asyncio
from tradestation import TradeStationClient


async def main():
    # Initialize client (uses env vars for credentials)
    async with TradeStationClient(is_demo=True) as client:
        # Get all accounts
        accounts = await client.get_accounts()
        print(f"Found {len(accounts.accounts)} accounts")
        
        # Get account balances
        account_id = accounts.accounts[0].account_id
        balances = await client.get_balances(account_id)
        for balance in balances.balances:
            print(f"Accoubt {balance.account_id},  Cash Balance: ${balance.cash_balance}")
        
        # Get positions
        positions = await client.get_positions(account_id)
        for position in positions.positions:
            print(f"{position.symbol}: {position.quantity} shares")


if __name__ == "__main__":
    asyncio.run(main())
