import asyncio
from tradestation import TradeStationClient
from tradestation.models import OrderRequest, TradeAction, TimeInForceRequest, Duration, OrderType, Order, Status


async def main():
    # Initialize client (uses env vars for credentials)
    async with TradeStationClient(is_demo=True) as client:
        accounts = await client.get_accounts()
        account_id = next(iter([account.account_id for account in accounts if account.account_type in ['Cash', 'Margin']]), None)
        if not account_id:
            print("No suitable account found to place order.")
            return
        print(f"Placing order in account {account_id}")
        
        order = OrderRequest(
            account_id=account_id,
            symbol="MSFT",
            quantity="100",
            order_type=OrderType.MARKET,
            trade_action=TradeAction.BUY,
            time_in_force=TimeInForceRequest(duration=Duration.GTC),
        )
        
        result = await client.place_order(order)
        
        print(f"Order Result: {result}")
        order = result.orders[0]
        print(f"Order ID: {order.order_id}, Message: {order.message}")
        
        async for order in client.stream_orders(account_id):
            if isinstance(order, Order) and order.order_id == order.order_id:
                print(f"Order Status Update: ID: {order.order_id}, Status: {order.status_description}")
                for leg in order.legs:
                    print(f"Order Update - ID: {leg.symbol}, Filled: {int(leg.quantity_ordered) - int(leg.quantity_remaining)}/{leg.quantity_ordered}")
                if order.status in [Status.FLL, Status.CAN, Status.REJ, Status.EXP, Status.OUT]:
                    print("Order completed with final status:", order.status_description)
                    break
            
if __name__ == "__main__":
    asyncio.run(main())
