"""Advanced place-order example for the TradeStation async client.

This example demonstrates how to place a bracket order (take-profit + stop-loss)
and a separate trailing-stop order using the asynchronous `TradeStationClient`.

What this script does (high level):
- Finds a demo/account to trade (Cash or Margin).
- Fetches current price for the symbol (MSFT) and derives example prices.
- Builds a primary LIMIT buy order for 100 shares and attaches:
  - A bracket (BRK) OSO containing a stop-market and a limit sell (take profit).
  - A NORMAL OSO containing a stop-market order with trailing-stop options for the remaining
    quantity.
- Submits the order and prints the result and any errors.
- Streams order updates for the created orders and prints status changes.

Prerequisites:
- Set the required credentials in environment variables as described in the library README
  (the client in this project reads credentials from env vars by default).
- Install this package or run from the repo with the proper PYTHONPATH so `tradestation` is importable.

Notes about safety and testing:
- This example sets `is_demo=True` when creating the client to use the demo environment.
  Make sure you understand the environment used before switching to live trading.
- The numeric prices here are computed from the last bar and converted to strings because
  the SDK models in this project expect string-encoded prices in many cases.

How to run:
  python examples/place_order_advanced.py

Read the inline comments in `main()` for details on each step.
"""

import asyncio
from tradestation import TradeStationClient
from tradestation.models import (
    OrderRequest,
    TradeAction,
    TimeInForceRequest,
    Duration,
    OrderType,
    Order,
    OrderRequestOSO,
    AdvancedOrderType,
    AdvancedOptions,
    TrailingStop,
    Status
)


async def main():
    """Run the example: create and place an advanced order, then stream updates.

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

        # 2) Get a recent market price for MSFT. We use the last bar's close.
        #    The client returns model objects; extract `close` from the last bar.
        quotes = await client.get_bars(symbol="MSFT")
        current_price = quotes[-1].close

        # 3) Compute example prices relative to current_price.
        #    Convert to strings if the SDK models expect string prices.
        limit_price = str(current_price - 2)
        take_profit_price = str(current_price + 5)
        stop_loss_price = str(current_price - 3)

        # 4) Build the main order request. This example creates a LIMIT buy for 100
        #    shares and attaches two OSOs:
        #    - A BRK OSO (bracket) containing a stop-market and a limit sell (take profit).
        #    - A NORMAL OSO containing a stop-market with a trailing stop option.
        order = OrderRequest(
            account_id=account_id,
            symbol="MSFT",
            quantity="100",
            order_type=OrderType.LIMIT,
            limit_price=limit_price,
            trade_action=TradeAction.BUY,
            time_in_force=TimeInForceRequest(duration=Duration.GTC),
            osos=[
                # Bracket (BRK) group: one stop and one limit (take-profit)
                OrderRequestOSO(
                    type=AdvancedOrderType.BRK,
                    orders=[
                        OrderRequest(
                            account_id=account_id,
                            symbol="MSFT",
                            quantity="50",
                            order_type=OrderType.STOP_MARKET,
                            trade_action=TradeAction.SELL,
                            time_in_force=TimeInForceRequest(duration=Duration.GTC),
                            stop_price=stop_loss_price,
                        ),
                        OrderRequest(
                            account_id=account_id,
                            symbol="MSFT",
                            quantity="50",
                            order_type=OrderType.LIMIT,
                            trade_action=TradeAction.SELL,
                            time_in_force=TimeInForceRequest(duration=Duration.GTC),
                            limit_price=take_profit_price,
                        ),
                    ],
                ),
                # Normal OSO: trailing stop for a portion of the position
                OrderRequestOSO(
                    type=AdvancedOrderType.NORMAL,
                    orders=[
                        OrderRequest(
                            account_id=account_id,
                            symbol="MSFT",
                            quantity="50",
                            order_type=OrderType.STOP_MARKET,
                            trade_action=TradeAction.SELL,
                            time_in_force=TimeInForceRequest(duration=Duration.GTC),
                            advanced_options=AdvancedOptions(
                                trailing_stop=TrailingStop(percent="1.0")
                            ),
                        )
                    ],
                ),
            ],
        )

        # 5) Place the order and collect the server response.
        result = await client.place_order(order)

        # `result.orders` contains the individual created orders (legs). The API
        # may also return `result.errors`.
        orders = result.orders
        errors = (result.errors or []) + [o for o in orders if getattr(o, "error", None) is not None]

        print(f"Placed {len(orders)} orders with {len(errors)} errors.")
        print("Orders:")
        for o in orders:
            print(f"    Order ID: {o.order_id}, Message: {o.message}")
        if errors:
            for err in errors:
                # entries in `errors` are order objects with an `error` field
                print(f"Order Error: {err.error}: {err.message}")

        # 6) Track order states. We maintain a dict mapping order_id -> last_known_status
        #    to detect terminal states (Filled, Cancelled, Rejected, Expired, etc.).
        order_tracking = {o.order_id: None for o in orders}
        terminal_statuses = {Status.FLL, Status.CAN, Status.REJ, Status.EXP, Status.OUT, Status.BRO}

        # 7) Stream updates for the account. This will yield order objects and
        #    status updates from the server. We check for orders that match the
        #    created order IDs, print status and leg fills, and track their state.
        #    Exit when all tracked orders reach a terminal state.
        print("\nStreaming order updates (will exit once all orders are terminal)...")
        async for update in client.stream_orders(account_id):
            if isinstance(update, Order) and update.order_id in order_tracking:
                status = update.status
                order_tracking[update.order_id] = status

                print(f"Order Status Update: ID: {update.order_id}, Status: {status}")
                for leg in update.legs:
                    print(f"  Leg - Symbol: {leg.symbol}, Ordered: {leg.quantity_ordered}, Remaining: {leg.quantity_remaining}")

                # Check if all tracked orders are now in a terminal state
                all_terminal = all(
                    order_status in terminal_statuses
                    for order_status in order_tracking.values()
                    if order_status is not None
                )
                if all_terminal and all(s is not None for s in order_tracking.values()):
                    print("\nAll orders have reached terminal state. Exiting stream.")
                    break


if __name__ == "__main__":
    asyncio.run(main())
