"""Simple place-order example for the TradeStation async client.

This example demonstrates how to place a basic market order using the
asynchronous `TradeStationClient` and monitor its execution status.

What this script does (high level):
- Finds a suitable account to trade (Cash or Margin).
- Places a MARKET buy order for 100 shares of MSFT.
- Streams order updates and prints status changes as the order executes.
- Automatically exits when the order reaches a terminal state (filled, cancelled, rejected, etc.).

Prerequisites:
- Set the required credentials in environment variables as described in the library README
  (the client in this project reads credentials from env vars by default).
- Install this package or run from the repo with the proper PYTHONPATH so `tradestation` is importable.

Notes about safety and testing:
- This example sets `is_demo=True` when creating the client to use the demo environment.
  Make sure you understand the environment used before switching to live trading.
- A MARKET order will execute at the best available price (or market price when market opens),
  so use caution when switching to live trading.

How to run:
  python examples/place_order.py

Read the inline comments in `main()` for details on each step.
"""

import asyncio
from tradestation import TradeStationClient
from tradestation.models import OrderRequest, TradeAction, TimeInForceRequest, Duration, OrderType, Order, Status


async def main():
    """Run the example: create and place a simple market order, then stream updates.

    Implementation details and steps are commented inline.
    """

    # Initialize the async client; the client will read credentials from env vars.
    # Use `is_demo=True` to place orders in the demo environment.
    async with TradeStationClient(is_demo=True) as client:
        # 1) Pick an account to use. We prefer 'Cash' or 'Margin' accounts.
        accounts = await client.get_accounts()
        account_id = next(
            iter([a.account_id for a in accounts if a.account_type in ["Cash", "Margin"]]),
            None,
        )
        if not account_id:
            print("No suitable account found to place order.")
            return
        print(f"Placing order in account {account_id}")

        # 2) Build a simple MARKET order. MARKET orders execute at the best available price.
        #    This order will buy 100 shares of MSFT as soon as the market allows.
        order = OrderRequest(
            account_id=account_id,
            symbol="MSFT",
            quantity="100",
            order_type=OrderType.MARKET,
            trade_action=TradeAction.BUY,
            time_in_force=TimeInForceRequest(duration=Duration.GTC),
        )

        # 3) Place the order and collect the server response.
        result = await client.place_order(order)

        print(f"Order Result: {result}")
        placed_order = result.orders[0]
        print(f"Order ID: {placed_order.order_id}, Message: {placed_order.message}")

        # 4) Define terminal statuses. We'll exit the stream when the order reaches one of these.
        terminal_statuses = {Status.FLL, Status.CAN, Status.REJ, Status.EXP, Status.OUT, Status.BRO}
        tracked_order_id = placed_order.order_id

        # 5) Stream updates for the account. This will yield order objects and
        #    status updates from the server. We check for our order and print
        #    status and leg fills. Exit when the order reaches a terminal state.
        print("\nStreaming order updates (will exit once order is terminal)...")
        async for update in client.stream_orders(account_id):
            if isinstance(update, Order) and update.order_id == tracked_order_id:
                print(
                    f"Order Status Update: ID: {update.order_id}, Status: {update.status_description}"
                )
                for leg in update.legs:
                    filled = int(leg.quantity_ordered) - int(leg.quantity_remaining)
                    print(
                        f"  Leg - Symbol: {leg.symbol}, Filled: {filled}/{leg.quantity_ordered}"
                    )

                # Check if order reached a terminal state
                if update.status in terminal_statuses:
                    print(f"\nOrder completed with final status: {update.status_description}")
                    break


if __name__ == "__main__":
    asyncio.run(main())
