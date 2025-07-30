from pydantic import Field
from pydantic import Field, model_rebuild
from typing import List
from typing import Literal
from typing import Optional


from pydantic import BaseModel

class SerializableModel(BaseModel):
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

    def to_dict(self):
        return self.model_dump(by_alias=True)

class Error(SerializableModel):
    trace_id: Optional[str] = Field(None, alias="TraceId")
    status_code: Optional[int] = Field(None, alias="StatusCode")
    message: Optional[str] = Field(None, alias="Message")

AccountID = str

class AccountDetail(SerializableModel):
    day_trading_qualified: Optional[bool] = Field(None, alias="DayTradingQualified", description="Indicates if the account is qualified to day trade as per compliance suitability in TradeStation. An account that is not Day Trading Qualified is subject to restrictions that will not allow it to become a pattern day trader.")
    enrolled_in_reg_tprogram: Optional[bool] = Field(None, alias="EnrolledInRegTProgram", description="For internal use only.  Identifies whether accounts is enrolled in Reg T program.")
    is_stock_locate_eligible: Optional[bool] = Field(None, alias="IsStockLocateEligible", description="True if this account is stock locate eligible; otherwise, false.")
    option_approval_level: Optional[int] = Field(None, alias="OptionApprovalLevel", description="Valid values are: `0`, `1`, `2`, `3`, `4`, and `5`.\n(Equities) The option approval level will determine what options strategies you will be able to employ in the account. In general terms, the levels are defined as follows:\nLevel 0 - No options trading allowed\nLevel 1 - Writing of Covered Calls, Buying Protective Puts\nLevel 2 - Level 1 + Buying Calls, Buying Puts, Writing Covered Puts\nLevel 3 - level 2+ Stock Option Spreads, Index Option Spreads, Butterfly Spreads, Condor Spreads, Iron Butterfly Spreads, Iron Condor Spreads\nLevel 4 - Level 3 + Writing of Naked Puts (Stock Options)\nLevel 5 - Level 4 + Writing of Naked Puts (Index Options), Writing of Naked Calls (Stock Options), Writing of Naked Calls (Index Options)")
    pattern_day_trader: Optional[bool] = Field(None, alias="PatternDayTrader", description="(Equities) Indicates whether you are considered a pattern day trader. As per FINRA rules, you will be considered a pattern day trader if you trade 4 or more times in 5 business days and your day-trading activities are greater than 6 percent of your total trading activity for that same five-day period. A pattern day trader must maintain a minimum equity of $25,000 on any day that the customer day trades. If the account falls below the $25,000 requirement, the pattern day trader will not be permitted to day trade until the account is restored to the $25,000 minimum equity level.")
    requires_buying_power_warning: Optional[bool] = Field(None, alias="RequiresBuyingPowerWarning", description="For internal use only. Identifies whether account is enrolled in the margin buying power warning program to receive alerts prior to placing an order which would exceed their buying power.")

class Account(SerializableModel):
    account_detail: Optional[AccountDetail] = Field(None, alias="AccountDetail")
    account_id: Optional[AccountID] = Field(None, alias="AccountID")
    account_type: Optional[str] = Field(None, alias="AccountType", description="The type of the TradeStation Account. Valid values are: `Cash`, `Margin`, `Futures`, and `DVP`.")
    alias: Optional[str] = Field(None, alias="Alias", description="A user specified name that identifies a TradeStation account. Omits if not set.")
    alt_id: Optional[str] = Field(None, alias="AltID", description="TradeStation account ID for accounts based in Japan. Omits if not set.")
    currency: Optional[str] = Field(None, alias="Currency", description="Currency associated with this account.")
    status: Optional[str] = Field(None, alias="Status", description="Status of a specific account:\n- Active\n- Closed\n- Closing Transaction Only\n- Margin Call - Closing Transactions Only\n- Inactive\n- Liquidating Transactions Only\n- Restricted\n- 90 Day Restriction-Closing Transaction Only")

class Accounts(SerializableModel):
    accounts: Optional[List[Account]] = Field(None, alias="Accounts")

class ErrorResponse(SerializableModel):
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `BadRequest`, `Unauthorized`, `Forbidden`, `TooManyRequests`, `InternalServerError`, `NotImplemented`, `ServiceUnavailable`, or `GatewayTimeout`.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")

class BalanceError(SerializableModel):
    account_id: Optional[str] = Field(None, alias="AccountID", description="The AccountID of the error, may contain multiple Account IDs in comma separated format.")
    error: Optional[str] = Field(None, alias="Error", description="The Error.")
    message: Optional[str] = Field(None, alias="Message", description="The error message.")

class BalanceDetail(SerializableModel):
    cost_of_positions: Optional[str] = Field(None, alias="CostOfPositions", description="(Equities) The cost used to calculate today's P/L.")
    day_trade_excess: Optional[str] = Field(None, alias="DayTradeExcess", description="(Equities): (Buying Power Available - Buying Power Used) / Buying Power Multiplier. (Futures): (Cash + UnrealizedGains) - Buying Power Used.")
    day_trade_margin: Optional[str] = Field(None, alias="DayTradeMargin", description="(Futures) Money field representing the current total amount of futures day trade margin.")
    day_trade_open_order_margin: Optional[str] = Field(None, alias="DayTradeOpenOrderMargin", description="(Futures) Money field representing the current amount of money reserved for open orders.")
    day_trades: Optional[str] = Field(None, alias="DayTrades", description="(Equities) The number of day trades placed in the account within the previous 4 trading days. A day trade refers to buying then selling or selling short then buying to cover the same security on the same trading day.")
    initial_margin: Optional[str] = Field(None, alias="InitialMargin", description="(Futures) Sum (Initial Margins of all positions in the given account).")
    maintenance_margin: Optional[str] = Field(None, alias="MaintenanceMargin", description="(Futures) Indicates the value of real-time maintenance margin.")
    maintenance_rate: Optional[str] = Field(None, alias="MaintenanceRate", description="Maintenance Margin Rate.")
    margin_requirement: Optional[str] = Field(None, alias="MarginRequirement", description="(Futures) Indicates the value of real-time account margin requirement.")
    open_order_margin: Optional[str] = Field(None, alias="OpenOrderMargin", description="(Futures) The dollar amount of Open Order Margin for the given futures account.")
    option_buying_power: Optional[str] = Field(None, alias="OptionBuyingPower", description="(Equities) The intraday buying power for options.")
    options_market_value: Optional[str] = Field(None, alias="OptionsMarketValue", description="(Equities) Market value of open positions.")
    overnight_buying_power: Optional[str] = Field(None, alias="OvernightBuyingPower", description="Only applies to equities. Real-time Overnight Marginable Equities Buying Power.")
    realized_profit_loss: Optional[str] = Field(None, alias="RealizedProfitLoss", description="Indicates the value of real-time account realized profit or loss.")
    required_margin: Optional[str] = Field(None, alias="RequiredMargin", description="(Equities) Total required margin for all held positions.")
    security_on_deposit: Optional[str] = Field(None, alias="SecurityOnDeposit", description="(Futures) The value of special securities that are deposited by the customer with the clearing firm for the sole purpose of increasing purchasing power in their trading account. This number will be reset daily by the account balances clearing file. The entire value of this field will increase purchasing power.")
    today_real_time_trade_equity: Optional[str] = Field(None, alias="TodayRealTimeTradeEquity", description="(Futures) The unrealized P/L for today. Unrealized P/L - BODOpenTradeEquity.")
    trade_equity: Optional[str] = Field(None, alias="TradeEquity", description="(Futures) The dollar amount of unrealized profit and loss for the given futures account. Same value as RealTimeUnrealizedGains.")
    unrealized_profit_loss: Optional[str] = Field(None, alias="UnrealizedProfitLoss", description="Indicates the value of real-time account unrealized profit or loss.")
    unsettled_funds: Optional[str] = Field(None, alias="UnsettledFunds", description="Unsettled Funds are funds that have been closed but not settled.")

class CurrencyDetail(SerializableModel):
    account_conversion_rate: Optional[str] = Field(None, alias="AccountConversionRate", description="Indicates the rate used to convert from the currency of the symbol to the currency of the account.")
    account_margin_requirement: Optional[str] = Field(None, alias="AccountMarginRequirement", description="Indicates the value of real-time account margin requirement.")
    cash_balance: Optional[str] = Field(None, alias="CashBalance", description="Indicates the value of real-time cash balance.")
    commission: Optional[str] = Field(None, alias="Commission", description="(Futures) The brokerage commission cost and routing fees (if applicable) for a trade based on the number of shares or contracts.")
    currency: Optional[str] = Field(None, alias="Currency", description="Currency is the currency this account is traded in.")
    initial_margin: Optional[str] = Field(None, alias="InitialMargin", description="Indicates the value of real-time initial margin.")
    maintenance_margin: Optional[str] = Field(None, alias="MaintenanceMargin", description="Indicates the value of real-time maintance margin.")
    realized_profit_loss: Optional[str] = Field(None, alias="RealizedProfitLoss", description="Indicates the value of real-time realized profit or loss.")
    unrealized_profit_loss: Optional[str] = Field(None, alias="UnrealizedProfitLoss", description="Indicates the value of real-time unrealized profit or loss.")

class Balance(SerializableModel):
    account_id: Optional[AccountID] = Field(None, alias="AccountID")
    account_type: Optional[str] = Field(None, alias="AccountType", description="The type of the account. Valid values are: `Cash`, `Margin`, `Futures` and `DVP`.")
    balance_detail: Optional[BalanceDetail] = Field(None, alias="BalanceDetail")
    buying_power: Optional[str] = Field(None, alias="BuyingPower", description="Buying Power available in the account.")
    cash_balance: Optional[str] = Field(None, alias="CashBalance", description="Indicates the value of real-time cash balance.")
    commission: Optional[str] = Field(None, alias="Commission", description="The brokerage commission cost and routing fees (if applicable) for a trade based on the number of shares or contracts.")
    currency_details: Optional[List[CurrencyDetail]] = Field(None, alias="CurrencyDetails", description="Only applies to futures. Collection of properties that describe balance characteristics in different currencies.")
    equity: Optional[str] = Field(None, alias="Equity", description="The real-time equity of the account.")
    market_value: Optional[str] = Field(None, alias="MarketValue", description="Market value of open positions.")
    todays_profit_loss: Optional[str] = Field(None, alias="TodaysProfitLoss", description="Unrealized profit and loss, for the current trading day, of all open positions.")
    uncleared_deposit: Optional[str] = Field(None, alias="UnclearedDeposit", description="The total of uncleared checks received by Tradestation for deposit.")

class Balances(SerializableModel):
    balances: Optional[List[Balance]] = Field(None, alias="Balances")
    errors: Optional[List[BalanceError]] = Field(None, alias="Errors")

class BODCurrencyDetail(SerializableModel):
    account_margin_requirement: Optional[str] = Field(None, alias="AccountMarginRequirement", description="The dollar amount of Beginning Day Margin for the given forex account.")
    account_open_trade_equity: Optional[str] = Field(None, alias="AccountOpenTradeEquity", description="The dollar amount of Beginning Day Trade Equity for the given account.")
    account_securities: Optional[str] = Field(None, alias="AccountSecurities", description="The value of special securities that are deposited by the customer with the clearing firm for the sole purpose of increasing purchasing power in their trading account. This number will be reset daily by the account balances clearing file. The entire value of this field will increase purchasing power.")
    cash_balance: Optional[str] = Field(None, alias="CashBalance", description="The dollar amount of the Beginning Day Cash Balance for the given account.")
    currency: Optional[str] = Field(None, alias="Currency", description="The currency of the entity.")
    margin_requirement: Optional[str] = Field(None, alias="MarginRequirement", description="The dollar amount of Beginning Day Margin for the given forex account.")
    open_trade_equity: Optional[str] = Field(None, alias="OpenTradeEquity", description="The dollar amount of Beginning Day Trade Equity for the given account.")
    securities: Optional[str] = Field(None, alias="Securities", description="Indicates the dollar amount of Beginning Day Securities")

class BODBalanceDetail(SerializableModel):
    account_balance: Optional[str] = Field(None, alias="AccountBalance", description="Only applies to equities. The amount of cash in the account at the beginning of the day.")
    cash_available_to_withdraw: Optional[str] = Field(None, alias="CashAvailableToWithdraw", description="Beginning of day value for cash available to withdraw.")
    day_trades: Optional[str] = Field(None, alias="DayTrades", description="Only applies to equities. The number of day trades placed in the account within the previous 4 trading days. A day trade refers to buying then selling or selling short then buying to cover the same security on the same trading day.")
    day_trading_marginable_buying_power: Optional[str] = Field(None, alias="DayTradingMarginableBuyingPower", description="Only applies to equities. The Intraday Buying Power with which the account started the trading day.")
    equity: Optional[str] = Field(None, alias="Equity", description="The total amount of equity with which you started the current trading day.")
    net_cash: Optional[str] = Field(None, alias="NetCash", description="The amount of cash in the account at the beginning of the day.")
    open_trade_equity: Optional[str] = Field(None, alias="OpenTradeEquity", description="Only applies to futures. Unrealized profit and loss at the beginning of the day.")
    option_buying_power: Optional[str] = Field(None, alias="OptionBuyingPower", description="Only applies to equities. Option buying power at the start of the trading day.")
    option_value: Optional[str] = Field(None, alias="OptionValue", description="Only applies to equities. Intraday liquidation value of option positions.")
    overnight_buying_power: Optional[str] = Field(None, alias="OvernightBuyingPower", description="(Equities) Overnight Buying Power (Regulation T) at the start of the trading day.")
    security_on_deposit: Optional[str] = Field(None, alias="SecurityOnDeposit", description="(Futures) The value of special securities that are deposited by the customer with the clearing firm for the sole purpose of increasing purchasing power in their trading account.")

class BODBalance(SerializableModel):
    account_id: Optional[AccountID] = Field(None, alias="AccountID")
    account_type: Optional[str] = Field(None, alias="AccountType", description="The account type of this account.")
    balance_detail: Optional[BODBalanceDetail] = Field(None, alias="BalanceDetail")
    currency_details: Optional[List[BODCurrencyDetail]] = Field(None, alias="CurrencyDetails", description="Only applies to futures. Contains beginning of day currency detail information which varies according to account type.")

class BalancesBOD(SerializableModel):
    bodbalances: Optional[List[BODBalance]] = Field(None, alias="BODBalances")
    errors: Optional[List[BalanceError]] = Field(None, alias="Errors")

class HistoricalOrder(OrderBase):
    status: Optional[HistoricalStatus] = Field(None, alias="Status")
    status_description: Optional[str] = Field(None, alias="StatusDescription", description="Description of the status.")
    stop_price: Optional[str] = Field(None, alias="StopPrice", description="The stop price for StopLimit and StopMarket orders.")
    trailing_stop: Optional[TrailingStop] = Field(None, alias="TrailingStop")
    unbundled_route_fee: Optional[str] = Field(None, alias="UnbundledRouteFee", description="Only applies to equities.  Will contain a value if the order has received a routing fee.")

class OrderError(SerializableModel):
    account_id: Optional[str] = Field(None, alias="AccountID", description="The AccountID of the error, may contain multiple Account IDs in comma separated format.")
    error: Optional[str] = Field(None, alias="Error", description="The Error.")
    message: Optional[str] = Field(None, alias="Message", description="The error message.")

class HistoricalOrders(SerializableModel):
    orders: Optional[List[HistoricalOrder]] = Field(None, alias="Orders")
    errors: Optional[List[OrderError]] = Field(None, alias="Errors")
    next_token: Optional[str] = Field(None, alias="NextToken", description="A token returned with paginated orders which can be used in a subsequent request to retrieve the next page.")

class OrderByIDError(SerializableModel):
    account_id: Optional[str] = Field(None, alias="AccountID", description="The AccountID of the error, may contain multiple Account IDs in comma separated format.")
    order_id: Optional[str] = Field(None, alias="OrderID", description="The OrderID of the error.")
    error: Optional[str] = Field(None, alias="Error", description="The Error.")
    message: Optional[str] = Field(None, alias="Message", description="The error message.")

class HistoricalOrdersById(SerializableModel):
    orders: Optional[List[HistoricalOrder]] = Field(None, alias="Orders")
    errors: Optional[List[OrderByIDError]] = Field(None, alias="Errors")

class Order(OrderBase):
    status: Optional[Status] = Field(None, alias="Status")
    status_description: Optional[str] = Field(None, alias="StatusDescription", description="Description of the status.")
    stop_price: Optional[str] = Field(None, alias="StopPrice", description="The stop price for StopLimit and StopMarket orders.")
    trailing_stop: Optional[TrailingStop] = Field(None, alias="TrailingStop")
    unbundled_route_fee: Optional[str] = Field(None, alias="UnbundledRouteFee", description="Only applies to equities.  Will contain a value if the order has received a routing fee.")

class Orders(SerializableModel):
    orders: Optional[List[Order]] = Field(None, alias="Orders")
    errors: Optional[List[OrderError]] = Field(None, alias="Errors")
    next_token: Optional[str] = Field(None, alias="NextToken", description="A token returned with paginated orders which can be used in a subsequent request to retrieve the next page.")

class OrdersById(SerializableModel):
    orders: Optional[List[Order]] = Field(None, alias="Orders")
    errors: Optional[List[OrderByIDError]] = Field(None, alias="Errors")

class PositionError(SerializableModel):
    account_id: Optional[str] = Field(None, alias="AccountID", description="The AccountID of the error, may contain multiple Account IDs in comma separated format.")
    error: Optional[str] = Field(None, alias="Error", description="The Error.")
    message: Optional[str] = Field(None, alias="Message", description="The error message.")

class PositionDirection(SerializableModel):
    pass

class PositionResponse(SerializableModel):
    account_id: Optional[AccountID] = Field(None, alias="AccountID")
    asset_type: Optional[Literal["STOCK", "STOCKOPTION", "FUTURE", "INDEXOPTION"]] = Field(None, alias="AssetType", description="Indicates the asset type of the position.")
    average_price: Optional[str] = Field(None, alias="AveragePrice", description="The average price of the position currently held.")
    bid: Optional[str] = Field(None, alias="Bid", description="The highest price a prospective buyer is prepared to pay at a particular time for a trading unit of a given symbol.")
    ask: Optional[str] = Field(None, alias="Ask", description="The price at which a security, futures contract, or other financial instrument is offered for sale.")
    conversion_rate: Optional[str] = Field(None, alias="ConversionRate", description="The currency conversion rate that is used in order to convert from the currency of the symbol to the currency of the account.")
    day_trade_requirement: Optional[str] = Field(None, alias="DayTradeRequirement", description="(Futures) DayTradeMargin used on open positions. Currently only calculated for futures positions. Other asset classes will have a 0 for this value.")
    expiration_date: Optional[str] = Field(None, alias="ExpirationDate", description="The UTC formatted expiration date of the future or option symbol, in the country the contract is traded in. The time portion of the value should be ignored.")
    initial_requirement: Optional[str] = Field(None, alias="InitialRequirement", description="Only applies to future and option positions. The margin account balance denominated in the symbol currency required for entering a position on margin.")
    maintenance_margin: Optional[str] = Field(None, alias="MaintenanceMargin", description="The margin account balance denominated in the account currency required for maintaining a position on margin.")
    last: Optional[str] = Field(None, alias="Last", description="The last price at which the symbol traded.")
    long_short: Optional[PositionDirection] = Field(None, alias="LongShort")
    mark_to_market_price: Optional[str] = Field(None, alias="MarkToMarketPrice", description="Only applies to equity and option positions. The MarkToMarketPrice value is the weighted average of the previous close price for the position quantity held overnight and the purchase price of the position quantity opened during the current market session. This value is used to calculate TodaysProfitLoss.")
    market_value: Optional[str] = Field(None, alias="MarketValue", description="The actual market value denominated in the symbol currency of the open position. This value is updated in real-time.")
    position_id: Optional[str] = Field(None, alias="PositionID", description="A unique identifier for the position.")
    quantity: Optional[str] = Field(None, alias="Quantity", description="The number of shares or contracts for a particular position. This value is negative for short positions.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="Symbol of the position.")
    timestamp: Optional[str] = Field(None, alias="Timestamp", description="Time the position was entered.")
    todays_profit_loss: Optional[str] = Field(None, alias="TodaysProfitLoss", description="Only applies to equity and option positions. This value will be included in the payload to convey the unrealized profit or loss denominated in the account currency on the position held, calculated using the MarkToMarketPrice.")
    total_cost: Optional[str] = Field(None, alias="TotalCost", description="The total cost denominated in the account currency of the open position.")
    unrealized_profit_loss: Optional[str] = Field(None, alias="UnrealizedProfitLoss", description="The unrealized profit or loss denominated in the symbol currency on the position held, calculated based on the average price of the position.")
    unrealized_profit_loss_percent: Optional[str] = Field(None, alias="UnrealizedProfitLossPercent", description="The unrealized profit or loss on the position expressed as a percentage of the initial value of the position.")
    unrealized_profit_loss_qty: Optional[str] = Field(None, alias="UnrealizedProfitLossQty", description="The unrealized profit or loss denominated in the account currency divided by the number of shares, contracts or units held.")

class Positions(SerializableModel):
    positions: Optional[List[PositionResponse]] = Field(None, alias="Positions")
    errors: Optional[List[PositionError]] = Field(None, alias="Errors")

class TradeAction(SerializableModel):
    pass

class OrderRequestLegs(SerializableModel):
    quantity: str = Field(..., alias="Quantity", description="The quantity of the order.")
    symbol: str = Field(..., alias="Symbol", description="The symbol used for this leg of the order.")
    trade_action: TradeAction = Field(..., alias="TradeAction")

class OrderType(SerializableModel):
    pass

class AdvancedOrderType(SerializableModel):
    pass

class OrderRequestOSO(SerializableModel):
    orders: List[OrderRequest] = Field(..., alias="Orders")
    type: AdvancedOrderType = Field(..., alias="Type")

class TrailingStop(SerializableModel):
    amount: Optional[str] = Field(None, alias="Amount", description="Currency Offset from current price. Note: Mutually exclusive with Percent.")
    percent: Optional[str] = Field(None, alias="Percent", description="Percentage offset from current price. Note: Mutually exclusive with Amount.")

class MarketActivationRules(SerializableModel):
    rule_type: Optional[str] = Field(None, alias="RuleType", description="Type of the activation rule. Currently only supports `Price`.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="Symbol that the rule is based on.")
    predicate: Optional[str] = Field(None, alias="Predicate", description="The predicate comparison for the market rule type. E.g. `Lt` (less than).\n- `Lt` - Less Than\n- `Lte` - Less Than or Equal\n- `Gt` - Greater Than\n- `Gte` - Greater Than or Equal")
    trigger_key: Optional[Literal["STT", "STTN", "SBA", "SAB", "DTT", "DTTN", "DBA", "DAB", "TTT", "TTTN", "TBA", "TAB"]] = Field(None, alias="TriggerKey", description="The ticks behavior for the activation rule. Rule descriptions can be obtained from [Get Activation Triggers](#operation/GetActivationTriggers).")
    price: Optional[str] = Field(None, alias="Price", description="Valid only for RuleType=\"Price\", the price at which the rule will trigger when the price hits ticks as specified by TriggerKey.")
    logic_operator: Optional[Literal["And", "Or"]] = Field(None, alias="LogicOperator", description="Relation with the previous activation rule when given a list of MarketActivationRules. Ignored for the first MarketActivationRule.")

class TimeUtc(SerializableModel):
    pass

class TimeActivationRules(SerializableModel):
    time_utc: Optional[TimeUtc] = Field(None, alias="TimeUtc")

class AdvancedOptions(SerializableModel):
    add_liquidity: Optional[bool] = Field(None, alias="AddLiquidity", description="This option allows you to place orders that will only add liquidity on the route you selected. To place an Add Liquidity order, the user must also select Book Only order type. Valid values `true` and `false`.  Valid for Equities only.")
    all_or_none: Optional[bool] = Field(None, alias="AllOrNone", description="Use this advanced order feature when you do not want a partial fill. Your order will be filled in its entirety or not at all. Valid values `true` and `false`.  Valid for Equities and Options.")
    book_only: Optional[bool] = Field(None, alias="BookOnly", description="This option restricts the destination you choose in the direct routing from re-routing your order to another destination. This type of order is useful in controlling your execution costs by avoiding fees the Exchanges can charge for rerouting your order to another market center. Valid values `true` and `false`.  Valid for Equities only.")
    discretionary_price: Optional[str] = Field(None, alias="DiscretionaryPrice", description="You can use this option to reflect a Bid/Ask at a lower/higher price than you are willing to pay using a specified price increment. Valid for `Limit` and `Stop Limit` orders only. Valid for Equities only.")
    market_activation_rules: Optional[List[MarketActivationRules]] = Field(None, alias="MarketActivationRules", description="Allows you to specify when an order will be placed based on the price action of one or more symbols.")
    non_display: Optional[bool] = Field(None, alias="NonDisplay", description="When you send a non-display order, it will not be reflected in either the Market Depth display or ECN books. Valid values `true` and `false`.  Valid for Equities only.")
    peg_value: Optional[str] = Field(None, alias="PegValue", description="This order type is useful to achieve a fair price in a fast or volatile market. Valid values `BEST` and `MID`. Valid for Equities only.")
    show_only_quantity: Optional[str] = Field(None, alias="ShowOnlyQuantity", description="Hides the true number of shares intended to be bought or sold. Valid for `Limit` and `StopLimit` order types. Not valid for all exchanges. For Equities and Futures.")
    time_activation_rules: Optional[List[TimeActivationRules]] = Field(None, alias="TimeActivationRules", description="Allows you to specify a time that an order will be placed.")
    trailing_stop: Optional[TrailingStop] = Field(None, alias="TrailingStop")

class Expiration(SerializableModel):
    pass

class Duration(SerializableModel):
    pass

class TimeInForceRequest(SerializableModel):
    duration: Duration = Field(..., alias="Duration")
    expiration: Optional[Expiration] = Field(None, alias="Expiration")

class OrderRequest(SerializableModel):
    account_id: AccountID = Field(..., alias="AccountID")
    advanced_options: Optional[AdvancedOptions] = Field(None, alias="AdvancedOptions")
    buying_power_warning: Optional[str] = Field(None, alias="BuyingPowerWarning", description="For internal use only. For TradeStation Margin accounts enrolled in the Reg-T program, clients should send\nconfirmation that the customer has been shown appropriate buying power warnings in advance of placing an order\nthat could potentially violate the account's buying power. Valid values are: `Enforce`, `Preconfirmed`, and\n`Confirmed`.")
    legs: Optional[List[OrderRequestLegs]] = Field(None, alias="Legs")
    limit_price: Optional[str] = Field(None, alias="LimitPrice", description="The limit price for this order.")
    osos: Optional[List[OrderRequestOSO]] = Field(None, alias="OSOs")
    order_confirm_id: Optional[str] = Field(None, alias="OrderConfirmID", description="A unique identifier regarding an order used to prevent duplicates. Must be unique per API key, per order, per user.")
    order_type: OrderType = Field(..., alias="OrderType")
    quantity: str = Field(..., alias="Quantity", description="The quantity of the order.")
    route: Optional[str] = Field(None, alias="Route", description="The route of the order. For Stocks and Options, Route value will default to `Intelligent` if no value is set. Routes can be obtained from [Get Routes](#operation/Routes).")
    stop_price: Optional[str] = Field(None, alias="StopPrice", description="The stop price for this order. If a TrailingStop amount or percent is passed in with the request (in the AdvancedOptions), and a StopPrice value is also passed in, the StopPrice value is ignored.")
    symbol: str = Field(..., alias="Symbol", description="The symbol used for this order.")
    time_in_force: TimeInForceRequest = Field(..., alias="TimeInForce")
    trade_action: TradeAction = Field(..., alias="TradeAction")
    model_rebuild()

class ExpirationDate(SerializableModel):
    pass

class CallPut(SerializableModel):
    pass

class OrderConfirmResponseLeg(SerializableModel):
    expiration_date: Optional[ExpirationDate] = Field(None, alias="ExpirationDate")
    option_type: Optional[CallPut] = Field(None, alias="OptionType")
    quantity: Optional[str] = Field(None, alias="Quantity", description="The quantity.")
    strike_price: Optional[str] = Field(None, alias="StrikePrice", description="The strike price for this option.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="The symbol name associated with this option.")
    trade_action: Optional[TradeAction] = Field(None, alias="TradeAction")

class OrderConfirmResponse(SerializableModel):
    account_currency: Optional[str] = Field(None, alias="AccountCurrency", description="The currency the account is traded in.")
    account_id: Optional[AccountID] = Field(None, alias="AccountID")
    add_liquidity: Optional[bool] = Field(None, alias="AddLiquidity", description="This option allows you to place orders that will only add liquidity on the route you selected. To place an Add Liquidity order, the user must also select Book Only order type. Valid values `true` and `false`.  Valid for Equities only.")
    all_or_none: Optional[bool] = Field(None, alias="AllOrNone", description="Use this advanced order feature when you do not want a partial fill. Your order will be filled in its entirety or not at all. Valid values `true` and `false`.  Valid for Equities and Options.")
    base_currency: Optional[str] = Field(None, alias="BaseCurrency", description="The base currency.")
    book_only: Optional[bool] = Field(None, alias="BookOnly", description="This option restricts the destination you choose in the direct routing from re-routing your order to another destination. This type of order is useful in controlling your execution costs by avoiding fees the Exchanges can charge for rerouting your order to another market center. Valid values `true` and `false`.  Valid for Equities only.")
    counter_currency: Optional[str] = Field(None, alias="CounterCurrency", description="The counter currency.")
    currency: Optional[str] = Field(None, alias="Currency", description="The currency used in this transaction.")
    debit_credit_estimated_cost: Optional[str] = Field(None, alias="DebitCreditEstimatedCost", description="The actual cost for Market orders and orders with conditions, such as Trailing Stop or Activation Rule orders. Takes into account wheather or not the transaction will result in a debit or credit to the user.")
    discretionary_price: Optional[str] = Field(None, alias="DiscretionaryPrice", description="You can use this option to reflect a Bid/Ask at a lower/higher price than you are willing to pay using a specified price increment. Valid for `Limit` and `Stop Limit` orders only. Valid for Equities only.")
    estimated_commission: Optional[str] = Field(None, alias="EstimatedCommission", description="An estimated value that is calculated using the published TradeStation commission schedule. Equity and Futures Orders.")
    estimated_cost: Optional[str] = Field(None, alias="EstimatedCost", description="The actual cost for Market orders and orders with conditions, such as Trailing Stop or Activation Rule orders.")
    estimated_price: Optional[str] = Field(None, alias="EstimatedPrice", description="An estimated value that is calculated using current market information. The actual cost for Market orders and orders with conditions, such as Trailing Stop or Activation Rule orders, may differ significantly from this estimate.")
    initial_margin_display: Optional[str] = Field(None, alias="InitialMarginDisplay", description="Estimated margin displayed for this transaction")
    legs: Optional[List[OrderConfirmResponseLeg]] = Field(None, alias="Legs")
    limit_price: Optional[str] = Field(None, alias="LimitPrice", description="The limit price for Limit orders.")
    non_display: Optional[bool] = Field(None, alias="NonDisplay", description="When you send a non-display order, it will not be reflected in either the Market Depth display or ECN books. Valid values `true` and `false`.  Valid for Equities only.")
    order_asset_category: Optional[Literal["EQUITY", "STOCKOPTION", "FUTURE"]] = Field(None, alias="OrderAssetCategory", description="Indicates the category of the order.")
    order_confirm_id: Optional[str] = Field(None, alias="OrderConfirmID", description="A unique identifier regarding an order used to prevent duplicates. Must be unique per API key, per order, per user.")
    peg_value: Optional[str] = Field(None, alias="PegValue", description="This order type is useful to achieve a fair price in a fast or volatile market. Valid values `BEST` and `MID`. Valid for Equities only.")
    product_currency: Optional[str] = Field(None, alias="ProductCurrency", description="The currency of the product.")
    route: Optional[str] = Field(None, alias="Route", description="The route of this transaction.")
    show_only_quantity: Optional[int] = Field(None, alias="ShowOnlyQuantity", description="Hides the true number of shares intended to be bought or sold. Valid for `Limit` and `StopLimit` order types. Not valid for all exchanges.")
    spread: Optional[str] = Field(None, alias="Spread", description="The option spread.")
    stop_price: Optional[str] = Field(None, alias="StopPrice", description="The stop price for open orders.")
    summary_message: Optional[str] = Field(None, alias="SummaryMessage", description="A summary message.")
    time_in_force: Optional[dict] = Field(None, alias="TimeInForce", description="TimeInForce defines the duration and duration timestamp.")
    trailing_stop: Optional[TrailingStop] = Field(None, alias="TrailingStop")
    underlying: Optional[str] = Field(None, alias="Underlying", description="Underlying symbol name.")

class OrderConfirmResponses(SerializableModel):
    confirmations: Optional[List[OrderConfirmResponse]] = Field(None, alias="Confirmations")

class GroupOrderRequest(SerializableModel):
    orders: List[OrderRequest] = Field(..., alias="Orders")
    type: str = Field(..., alias="Type", description="The group order type.  Valid values are: `BRK`, `OCO`, and `NORMAL`.")

class OrderResponse(SerializableModel):
    error: Optional[str] = Field(None, alias="Error")
    message: Optional[str] = Field(None, alias="Message")
    order_id: Optional[str] = Field(None, alias="OrderID")

class OrderResponses(SerializableModel):
    errors: Optional[List[OrderResponse]] = Field(None, alias="Errors")
    orders: Optional[List[OrderResponse]] = Field(None, alias="Orders")

class MarketActivationRulesReplace(SerializableModel):
    clear_all: Optional[bool] = Field(None, alias="ClearAll", description="If 'True', removes all activation rules when replacing the order and ignores any rules sent in `Rules`.")
    rules: Optional[List[MarketActivationRules]] = Field(None, alias="Rules")

class TimeActivationRulesReplace(SerializableModel):
    clear_all: Optional[bool] = Field(None, alias="ClearAll", description="If 'True', removes all activation rules when replacing the order and ignores any rules sent in `Rules`.")
    rules: Optional[List[TimeActivationRules]] = Field(None, alias="Rules")

class AdvancedOptionsReplace(SerializableModel):
    show_only_quantity: Optional[str] = Field(None, alias="ShowOnlyQuantity", description="Hides the true number of shares intended to be bought or sold. Valid for `Limit` and `StopLimit` order types. Not valid for all exchanges. For Equities and Futures.")
    trailing_stop: Optional[TrailingStop] = Field(None, alias="TrailingStop")
    market_activation_rules: Optional[MarketActivationRulesReplace] = Field(None, alias="MarketActivationRules", description="Allows you to specify when an order will be placed based on the price action of one or more symbols.")
    time_activation_rules: Optional[TimeActivationRulesReplace] = Field(None, alias="TimeActivationRules", description="Allows you to specify a time that an order will be placed.")

class OrderReplaceRequest(SerializableModel):
    limit_price: Optional[str] = Field(None, alias="LimitPrice", description="The limit price for this order.")
    stop_price: Optional[str] = Field(None, alias="StopPrice", description="The stop price for this order. If a TrailingStop amount or percent is passed in with the request (in the AdvancedOptions), and a StopPrice value is also passed in, the StopPrice value is ignored.")
    order_type: Optional[str] = Field(None, alias="OrderType", description="The order type of this order. Order type can only be updated to `Market`.")
    quantity: Optional[str] = Field(None, alias="Quantity", description="The quantity of this order.")
    advanced_options: Optional[AdvancedOptionsReplace] = Field(None, alias="AdvancedOptions")

class TimeStamp(SerializableModel):
    pass

class Bar(SerializableModel):
    close: Optional[str] = Field(None, alias="Close", description="The close price of the current bar.")
    down_ticks: Optional[int] = Field(None, alias="DownTicks", description="A trade made at a price less than the previous trade price or at a price equal to the previous trade price.")
    down_volume: Optional[int] = Field(None, alias="DownVolume", description="Volume traded on downticks. A tick is considered a downtick if the previous tick was a downtick or the price is lower than the previous tick.")
    epoch: Optional[int] = Field(None, alias="Epoch", description="The Epoch time.")
    high: Optional[str] = Field(None, alias="High", description="The high price of the current bar.")
    is_end_of_history: Optional[bool] = Field(None, alias="IsEndOfHistory", description="Conveys that all historical bars in the request have been delivered.")
    is_realtime: Optional[bool] = Field(None, alias="IsRealtime", description="Set when there is data in the bar and the data is being built in \"real time\" from a trade.")
    low: Optional[str] = Field(None, alias="Low", description="The low price of the current bar.")
    open: Optional[str] = Field(None, alias="Open", description="The open price of the current bar.")
    open_interest: Optional[str] = Field(None, alias="OpenInterest", description="For Options or Futures only. Number of open contracts.")
    time_stamp: Optional[TimeStamp] = Field(None, alias="TimeStamp")
    total_ticks: Optional[int] = Field(None, alias="TotalTicks", description="Total number of ticks (upticks and downticks together).")
    total_volume: Optional[str] = Field(None, alias="TotalVolume", description="The sum of up volume and down volume.")
    unchanged_ticks: Optional[int] = Field(None, alias="UnchangedTicks", description="This field is deprecated, and its value will always be zero.")
    unchanged_volume: Optional[int] = Field(None, alias="UnchangedVolume", description="This field is deprecated, and its value will always be zero.")
    up_ticks: Optional[int] = Field(None, alias="UpTicks", description="A trade made at a price greater than the previous trade price, or at a price equal to the previous trade price.")
    up_volume: Optional[int] = Field(None, alias="UpVolume", description="Volume traded on upticks. A tick is considered an uptick if the previous tick was an uptick or the price is higher than the previous tick.")
    bar_status: Optional[str] = Field(None, alias="BarStatus", description="Indicates if bar is Open or Closed.")

class Bars(SerializableModel):
    bars: Optional[List[Bar]] = Field(None, alias="Bars")

class Heartbeat(SerializableModel):
    heartbeat: Optional[int] = Field(None, alias="Heartbeat", description="The heartbeat, sent to indicate that the stream is alive, although data is not actively being sent. A heartbeat will be sent after 5 seconds on an idle stream.")
    timestamp: Optional[str] = Field(None, alias="Timestamp", description="Timestamp represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard. \nE.g. `2023-01-01T23:30:30Z`.")

class StreamErrorResponse(SerializableModel):
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `BadRequest`, `DualLogon`, `GoAway` or `InternalServerError`. When the server is about to shut down, \"GoAway\" is returned to indicate that the stream will close because of server shutdown, and that a new stream will need to be started by the client.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")

class SymbolNames(SerializableModel):
    symbol_names: Optional[List[str]] = Field(None, alias="SymbolNames")

class AssetType(SerializableModel):
    pass

class IncrementScheduleRow(SerializableModel):
    increment: Optional[str] = Field(None, alias="Increment", description="The incremental value.")
    starts_at: Optional[str] = Field(None, alias="StartsAt", description="The initial value to start incrementing from.")

class QuantityFormat(SerializableModel):
    format: Optional[Literal["Decimal"]] = Field(None, alias="Format", description="The format of the quantity.")
    decimals: Optional[str] = Field(None, alias="Decimals", description="The number of decimals precision, applies to the `Decimal` format only.")
    increment_style: Optional[str] = Field(None, alias="IncrementStyle", description="The incremental style. Valid values are: `Simple` and `Schedule`.")
    increment: Optional[str] = Field(None, alias="Increment", description="The decimal increment for all quantity movements, applies to the `Simple` Increment Style only.")
    increment_schedule: Optional[List[IncrementScheduleRow]] = Field(None, alias="IncrementSchedule")
    minimum_trade_quantity: Optional[str] = Field(None, alias="MinimumTradeQuantity", description="The minimum quantity of an asset that can be traded.")

class PriceFormat(SerializableModel):
    format: Optional[Literal["Decimal", "Fraction", "SubFraction"]] = Field(None, alias="Format", description="The format of the price.")
    decimals: Optional[str] = Field(None, alias="Decimals", description="The number of decimals precision, applies to the `Decimal` format only.")
    fraction: Optional[str] = Field(None, alias="Fraction", description="The denominator of the single fraction, i.e. `1/Fraction`, applies to the `Fraction` format only.")
    sub_fraction: Optional[str] = Field(None, alias="SubFraction", description="The additional fraction of a fraction denominator, applies to the `SubFraction` format only.")
    increment_style: Optional[Literal["Simple", "Schedule"]] = Field(None, alias="IncrementStyle", description="The style of increment for price movements.")
    increment: Optional[str] = Field(None, alias="Increment", description="The decimal increment for all price movements, applies to the `Simple` Increment Style only.")
    increment_schedule: Optional[List[IncrementScheduleRow]] = Field(None, alias="IncrementSchedule")
    point_value: Optional[str] = Field(None, alias="PointValue", description="The symbol's point value.")

class SymbolDetail(SerializableModel):
    asset_type: Optional[AssetType] = Field(None, alias="AssetType")
    country: Optional[str] = Field(None, alias="Country", description="The country of the exchange where the symbol is listed.")
    currency: Optional[str] = Field(None, alias="Currency", description="Displays the type of base currency for the selected symbol.")
    description: Optional[str] = Field(None, alias="Description", description="Displays the full name of the symbol, special characters may be formatted in unicode.")
    exchange: Optional[str] = Field(None, alias="Exchange", description="Name of exchange where this symbol is traded.")
    expiration_date: Optional[str] = Field(None, alias="ExpirationDate", description="The UTC formatted expiration date of a future or option symbol, in the country the contract is traded in. The time portion of the value should be ignored.")
    future_type: Optional[str] = Field(None, alias="FutureType", description="Displays the type of future contract the symbol represents, futures only.")
    option_type: Optional[CallPut] = Field(None, alias="OptionType")
    price_format: Optional[PriceFormat] = Field(None, alias="PriceFormat")
    quantity_format: Optional[QuantityFormat] = Field(None, alias="QuantityFormat")
    root: Optional[str] = Field(None, alias="Root", description="Displays the symbol root, e.g. `ES` for Futures symbol `@ESH21`, `OEX` for IndexOption `OEX 210129C1750`, and `AAPL` for StockOption `AAPL 210129C137`.")
    strike_price: Optional[str] = Field(None, alias="StrikePrice", description="For an Option symbol, the Strike Price for the Put or Call.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="The Symbol name or abbreviation.")
    underlying: Optional[str] = Field(None, alias="Underlying", description="The financial instrument on which an Options contract is based or derived. Can also apply to some Futures symbols, like continuous Futures contracts, e.g. `ESH21` for `@ES`.")

class SymbolDetailsErrorResponse(SerializableModel):
    error: Optional[str] = Field(None, alias="Error", description="The Error.")
    message: Optional[str] = Field(None, alias="Message", description="The error message.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="The requested symbol.")

class SymbolDetailsResponse(SerializableModel):
    errors: Optional[List[SymbolDetailsErrorResponse]] = Field(None, alias="Errors")
    symbols: Optional[List[SymbolDetail]] = Field(None, alias="Symbols")

class ActivationTrigger(SerializableModel):
    key: Optional[str] = Field(None, alias="Key", description="Value used in the `TriggerKey` property of `MarketActivationRules` in the `AdvancedOptions` for an order. Valid Values are: `STT`, `STTN`, `SBA`, `SAB`, `DTT`, `DTTN`, `DBA`, `DAB`, `TTT`, `TTTN`, `TBA`, and `TAB`.")
    name: Optional[str] = Field(None, alias="Name")
    description: Optional[str] = Field(None, alias="Description")

class ActivationTriggers(SerializableModel):
    activation_triggers: Optional[List[ActivationTrigger]] = Field(None, alias="ActivationTriggers")

class Routes(SerializableModel):
    id: Optional[str] = Field(None, alias="Id", description="The ID that must be sent in the optional Route property of a POST order request, when specifying a route for an order.")
    name: Optional[str] = Field(None, alias="Name", description="The name of the route.")
    asset_types: Optional[List[str]] = Field(None, alias="AssetTypes", description="The asset type of the route. Valid Values are: `STOCK`, `FUTURE`, `STOCKOPTION`, and `INDEXOPTION`.")

class OrderRelationship(SerializableModel):
    order_id: Optional[str] = Field(None, alias="OrderID", description="The order ID of the linked order.")
    relationship: Optional[str] = Field(None, alias="Relationship", description="Describes the relationship of a linked order within a group order to the current returned order. Valid Values are: `BRK`, `OSP` (linked parent), `OSO` (linked child), and `OCO`.")

class OrderLeg(SerializableModel):
    asset_type: Optional[Literal["UNKNOWN", "STOCK", "STOCKOPTION", "FUTURE", "FUTUREOPTION", "FOREX", "CURRENCYOPTION", "INDEX", "INDEXOPTION"]] = Field(None, alias="AssetType", description="Indicates the asset type of the order.")
    buy_or_sell: Optional[str] = Field(None, alias="BuyOrSell", description="Identifies whether the order is a buy or sell. Valid values are `Buy`, `Sell`, `SellShort`, or `BuyToCover`.")
    exec_quantity: Optional[str] = Field(None, alias="ExecQuantity", description="Number of shares that have been executed.")
    execution_price: Optional[str] = Field(None, alias="ExecutionPrice", description="The price at which order execution occurred.")
    expiration_date: Optional[dict] = Field(None, alias="ExpirationDate", description="The expiration date of the future or option symbol.")
    open_or_close: Optional[str] = Field(None, alias="OpenOrClose", description="What kind of order leg - Opening or Closing.")
    option_type: Optional[str] = Field(None, alias="OptionType", description="Present for options. Valid values are \"CALL\" and \"PUT\".")
    quantity_ordered: Optional[str] = Field(None, alias="QuantityOrdered", description="Number of shares or contracts being purchased or sold.")
    quantity_remaining: Optional[str] = Field(None, alias="QuantityRemaining", description="In a partially filled order, this is the number of shares or contracts that were unfilled.")
    strike_price: Optional[str] = Field(None, alias="StrikePrice", description="Present for options. The price at which the holder of an options contract can buy or sell the underlying asset.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="Symbol for the leg order.")
    underlying: Optional[str] = Field(None, alias="Underlying", description="Underlying Symbol associated. Only applies to Futures and Options.")

class ExpirationResponse(SerializableModel):
    pass

class OrderBase(SerializableModel):
    account_id: Optional[AccountID] = Field(None, alias="AccountID")
    advanced_options: Optional[str] = Field(None, alias="AdvancedOptions", description="Will display a value when the order has advanced order rules associated with it or\nis part of a bracket order. Valid Values are: `CND`, `AON`, `TRL`, `SHWQTY`, `DSCPR`, `NON`, `PEGVAL`, `BKO`, `PSO`\n* `AON` - All or None\n* `BKO` - Book Only\n* `CND` - Activation Rule\n* `DSCPR=<Price>` - Discretionary price\n* `NON` - Non-Display\n* `PEGVAL=<Value>` - Peg Value\n* `PSO` - Add Liquidity\n* `SHWQTY=<quantity>` - Show Only\n* `TRL` - Trailing Stop")
    closed_date_time: Optional[str] = Field(None, alias="ClosedDateTime", description="The Closed Date Time of this order.")
    commission_fee: Optional[str] = Field(None, alias="CommissionFee", description="The actual brokerage commission cost and routing fees (if applicable) for a trade based on the number of shares or contracts.")
    conditional_orders: Optional[List[OrderRelationship]] = Field(None, alias="ConditionalOrders", description="Describes the relationship between linked orders in a group and this order.")
    conversion_rate: Optional[str] = Field(None, alias="ConversionRate", description="Indicates the rate used to convert from the currency of the symbol to the currency of the account. Omits if not set.")
    currency: Optional[str] = Field(None, alias="Currency", description="Currency used to complete the Order.")
    duration: Optional[str] = Field(None, alias="Duration", description="The amount of time for which an order is valid.")
    filled_price: Optional[str] = Field(None, alias="FilledPrice", description="At the top level, this is the average fill price. For expanded levels, this is the actual execution price.")
    good_till_date: Optional[str] = Field(None, alias="GoodTillDate", description="For GTC, GTC+, GTD and GTD+ order durations. The date the order will expire on in UTC format. The time portion, if \"T00:00:00Z\", should be ignored.")
    group_name: Optional[str] = Field(None, alias="GroupName", description="It can be used to identify orders that are part of the same bracket.")
    legs: Optional[List[OrderLeg]] = Field(None, alias="Legs", description="An array of legs associated with this order.")
    market_activation_rules: Optional[List[MarketActivationRules]] = Field(None, alias="MarketActivationRules", description="Allows you to specify when an order will be placed based on the price action of one or more symbols.")
    time_activation_rules: Optional[List[TimeActivationRules]] = Field(None, alias="TimeActivationRules", description="Allows you to specify a time that an order will be placed.")
    limit_price: Optional[str] = Field(None, alias="LimitPrice", description="The limit price for Limit and Stop Limit orders.")
    opened_date_time: Optional[str] = Field(None, alias="OpenedDateTime", description="Time the order was placed.")
    order_id: Optional[str] = Field(None, alias="OrderID", description="The order ID of this order.")
    order_type: Optional[OrderType] = Field(None, alias="OrderType")
    price_used_for_buying_power: Optional[str] = Field(None, alias="PriceUsedForBuyingPower", description="Price used for the buying power calculation of the order.")
    reject_reason: Optional[str] = Field(None, alias="RejectReason", description="If an order has been rejected, this will display the rejection. reason")
    routing: Optional[str] = Field(None, alias="Routing", description="Identifies the routing selection made by the customer when placing the order.")
    show_only_quantity: Optional[str] = Field(None, alias="ShowOnlyQuantity", description="Hides the true number of shares intended to be bought or sold. Valid for `Limit` and `StopLimit` order types. Not valid for all exchanges.")
    spread: Optional[str] = Field(None, alias="Spread", description="The spread type for an option order.")

class Status(SerializableModel):
    pass

class HistoricalStatus(SerializableModel):
    pass

class Expiration1(SerializableModel):
    date: Optional[str] = Field(None, alias="Date", description="Timestamp represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard. E.g. `2021-12-17T00:00:00Z`.")
    type: Optional[str] = Field(None, alias="Type", description="Expiration Type, e.g. `Weekly`, `Monthly`, `Quarterly`, `EOM`, or `Other`.")

class Expirations(SerializableModel):
    expirations: Optional[List[Expiration1]] = Field(None, alias="Expirations")

class RiskRewardAnalysisInputLeg(SerializableModel):
    symbol: str = Field(..., alias="Symbol", description="Option contract symbol or underlying symbol to be traded for this leg.")
    quantity: int = Field(..., alias="Quantity", description="The number of option contracts to buy or sell for this leg. The value cannot be zero.")
    trade_action: Literal["BUY", "SELL"] = Field(..., alias="TradeAction", description="The kind of trade to place for this leg. Value values are `BUY` and `SELL`.")

class RiskRewardAnalysisInput(SerializableModel):
    spread_price: Optional[float] = Field(None, alias="SpreadPrice", description="The quoted price for the option spread trade.")
    legs: Optional[List[RiskRewardAnalysisInputLeg]] = Field(None, alias="Legs", description="The legs of the option spread trade. If more than one leg is specified, the expiration dates must all be the same. In addition, leg symbols must be of type stock, stock option, or index option.")

class RiskRewardAnalysisResult(SerializableModel):
    max_gain_is_infinite: Optional[bool] = Field(None, alias="MaxGainIsInfinite", description="Indicates whether the maximum gain can be infinite.")
    adjusted_max_gain: Optional[str] = Field(None, alias="AdjustedMaxGain", description="The adjusted maximum gain (if it is not infinite).")
    max_loss_is_infinite: Optional[bool] = Field(None, alias="MaxLossIsInfinite", description="Indicates whether the maximum loss can be infinite.")
    adjusted_max_loss: Optional[str] = Field(None, alias="AdjustedMaxLoss", description="The adjusted maximum loss (if it is not infinite).")
    breakeven_points: Optional[List[str]] = Field(None, alias="BreakevenPoints", description="Market price that the underlying security must reach for the trade to avoid a loss.")

class SpreadLeg(SerializableModel):
    symbol: Optional[str] = Field(None, alias="Symbol", description="Option contract symbol or underlying symbol to be traded for this leg.")
    ratio: Optional[int] = Field(None, alias="Ratio", description="The number of option contracts or underlying shares for this leg, relative to the other legs.\nA positive number represents a buy trade and a negative number represents a sell trade.\nFor example, a Butterfly spread can be represented using ratios of 1, -2, and 1:\nbuy 1 contract of the first leg, sell 2 contracts of the second leg, and buy 1 contract of the third leg.")
    strike_price: Optional[str] = Field(None, alias="StrikePrice", description="The strike price of the option contract for this leg.")
    expiration: Optional[str] = Field(None, alias="Expiration", description="Date on which the contract expires, e.g. `2021-12-17T00:00:00Z`.")
    option_type: Optional[str] = Field(None, alias="OptionType", description="The option type. It can be `Call` or `Put`.")
    asset_type: Optional[str] = Field(None, alias="AssetType", description="The asset category for this leg.")

class Spread(SerializableModel):
    delta: Optional[str] = Field(None, alias="Delta", description="The expected change in an option position’s value resulting from a one point increase in the price of the underlying security.")
    theta: Optional[str] = Field(None, alias="Theta", description="The expected decline in an option position’s value resulting from the passage of one day’s time, holding all other variables (price of the underlying, volatility, etc.) constant.")
    gamma: Optional[str] = Field(None, alias="Gamma", description="The expected change in an option position’s delta resulting from a one point increase in the price of the underlying security.")
    rho: Optional[str] = Field(None, alias="Rho", description="The expected change in an option position’s value resulting from an increase of one percentage point in the risk-free interest rate (e.g. an increase from 3% to 4%).")
    vega: Optional[str] = Field(None, alias="Vega", description="The expected change in an option position’s value resulting from an increase of one percentage point in the volatility of the underlying security (e.g. an increase from 26% to 27%).")
    implied_volatility: Optional[str] = Field(None, alias="ImpliedVolatility", description="The volatility of the underlying implied by an option position’s current price.")
    intrinsic_value: Optional[str] = Field(None, alias="IntrinsicValue", description="The value of an option position exclusive of the position’s time value.  The value of the option position if it were to expire immediately.")
    extrinsic_value: Optional[str] = Field(None, alias="ExtrinsicValue", description="The time value of an option position.  The market value of an option position minus the position’s intrinsic value.")
    theoretical_value: Optional[str] = Field(None, alias="TheoreticalValue", description="The value of an option position based on a theoretical model of option prices (e.g., the Bjerksund-Stensland model).  Calculated using volatility of the underlying.")
    probability_itm: Optional[str] = Field(None, alias="ProbabilityITM", description="The calculated probability that an option position will have intrinsic value at expiration.  Calculated using volatility of the underlying.")
    probability_otm: Optional[str] = Field(None, alias="ProbabilityOTM", description="The calculated probability that an option position will not have intrinsic value at expiration.  Calculated using volatility of the underlying.")
    probability_be: Optional[str] = Field(None, alias="ProbabilityBE", description="The calculated probability that an option position will have a value at expiration that is equal to or greater than the position’s current cost.  Calculated using volatility of the underlying.")
    probability_itm_iv: Optional[str] = Field(None, alias="ProbabilityITM_IV", description="The calculated probability that an option position will have intrinsic value at expiration.  Calculated using implied volatility.")
    probability_otm_iv: Optional[str] = Field(None, alias="ProbabilityOTM_IV", description="The calculated probability that an option position will not have intrinsic value at expiration.  Calculated using implied volatility.")
    probability_be_iv: Optional[str] = Field(None, alias="ProbabilityBE_IV", description="The calculated probability that an option position will have a value at expiration that is equal to or greater than the position’s current cost.  Calculated using implied volatility.")
    theoretical_value_iv: Optional[str] = Field(None, alias="TheoreticalValue_IV", description="The value of an option position based on a theoretical model of option prices (e.g., the Bjerksund-Stensland model).  Calculated using implied volatility.")
    standard_deviation: Optional[str] = Field(None, alias="StandardDeviation", description="1 standard deviation of the option spread. Calculated using implied volatility.")
    daily_open_interest: Optional[int] = Field(None, alias="DailyOpenInterest", description="Total number of open contracts for the option spread.  This value is updated daily.")
    ask: Optional[str] = Field(None, alias="Ask", description="Ask price. The price a seller is willing to accept for the option spread.")
    bid: Optional[str] = Field(None, alias="Bid", description="Bid price. The price a buyer is willing to pay for the option spread.")
    mid: Optional[str] = Field(None, alias="Mid", description="Mathematical average between `Ask` and `Bid`.")
    ask_size: Optional[int] = Field(None, alias="AskSize", description="Amount of security for the given `Ask` price.")
    bid_size: Optional[int] = Field(None, alias="BidSize", description="Amount of security for the given `Bid` price.")
    close: Optional[str] = Field(None, alias="Close", description="The last traded price for the option spread.  This value only updates during the official market session.")
    high: Optional[str] = Field(None, alias="High", description="Today's highest price for the option spread.")
    last: Optional[str] = Field(None, alias="Last", description="The last traded price for the option spread.")
    low: Optional[str] = Field(None, alias="Low", description="Today's lowest traded price for the option spread.")
    net_change: Optional[str] = Field(None, alias="NetChange", description="Difference between prior `Close` price and current `Close` price for the option spread.")
    net_change_pct: Optional[str] = Field(None, alias="NetChangePct", description="Percentage changed between prior `Close` price and current `Close` price for the option spread.")
    open: Optional[str] = Field(None, alias="Open", description="The initial price for the option spread during the official market session.")
    previous_close: Optional[str] = Field(None, alias="PreviousClose", description="Prior day's Closing price.")
    volume: Optional[int] = Field(None, alias="Volume", description="The number of contracts traded today.")
    side: Optional[str] = Field(None, alias="Side", description="Option Chain Side. It can be `Call`, `Put`, or `Both`.")
    strikes: Optional[List[str]] = Field(None, alias="Strikes", description="The strike prices for the option contracts in the legs of this spread.")
    legs: Optional[List[SpreadLeg]] = Field(None, alias="Legs", description="The legs of the option spread.")

class SpreadType(SerializableModel):
    name: Optional[str] = Field(None, alias="Name", description="Name of the spread type.")
    strike_interval: Optional[bool] = Field(None, alias="StrikeInterval", description="A true value indicates the spread type is comprised of multiple strike prices. If this is the case, the `strikeInterval` parameter can be used with the [Get Option Chain](#operation/GetOptionChain) and [Get Option Strikes](#operation/GetOptionStrikes) endpoints to specify the interval between the strikes of a spread.")
    expiration_interval: Optional[bool] = Field(None, alias="ExpirationInterval", description="Indicates whether this spread type uses multiple expirations.")

class SpreadTypes(SerializableModel):
    spread_types: Optional[List[SpreadType]] = Field(None, alias="SpreadTypes")

class Strikes(SerializableModel):
    spread_type: Optional[str] = Field(None, alias="SpreadType", description="Name of the spread type for these strikes.")
    strikes: Optional[List[List[str]]] = Field(None, alias="Strikes", description="Array of the strike prices for this spread type. Each element in the Strikes array is an array of strike prices for a single spread.")

class MarketFlags(SerializableModel):
    is_bats: Optional[bool] = Field(None, alias="IsBats", description="Is Bats.")
    is_delayed: Optional[bool] = Field(None, alias="IsDelayed", description="Is delayed.")
    is_halted: Optional[bool] = Field(None, alias="IsHalted", description="Is halted.")
    is_hard_to_borrow: Optional[bool] = Field(None, alias="IsHardToBorrow", description="Is hard to borrow.")

class Quote(SerializableModel):
    ask: Optional[str] = Field(None, alias="Ask", description="The price at which a security, futures contract, or other financial instrument is offered for sale.")
    ask_size: Optional[str] = Field(None, alias="AskSize", description="The number of trading units that prospective sellers are prepared to sell.")
    bid: Optional[str] = Field(None, alias="Bid", description="The highest price a prospective buyer is prepared to pay at a particular time for a trading unit of a given symbol.")
    bid_size: Optional[str] = Field(None, alias="BidSize", description="The number of trading units that prospective buyers are prepared to purchase for a symbol.")
    close: Optional[str] = Field(None, alias="Close", description="The closing price of the day.")
    daily_open_interest: Optional[str] = Field(None, alias="DailyOpenInterest", description="The total number of open or outstanding (not closed or delivered) options and/or futures contracts that exist on a given day, delivered on a particular day.")
    high: Optional[str] = Field(None, alias="High", description="The highest price of the day.")
    low: Optional[str] = Field(None, alias="Low", description="The lowest price of the day.")
    high52_week: Optional[str] = Field(None, alias="High52Week", description="The highest price of the past 52 weeks.")
    high52_week_timestamp: Optional[str] = Field(None, alias="High52WeekTimestamp", description="Date of the highest price in the past 52 week.")
    last: Optional[str] = Field(None, alias="Last", description="The last price at which the symbol traded.")
    min_price: Optional[str] = Field(None, alias="MinPrice", description="The minimum price a commodity futures contract may be traded for the current session.")
    max_price: Optional[str] = Field(None, alias="MaxPrice", description="The maximum price a commodity futures contract may be traded for the current session.")
    first_notice_date: Optional[str] = Field(None, alias="FirstNoticeDate", description="The day after which an investor who has purchased a futures contract may be required to take physical delivery of the contracts underlying commodity.")
    last_trading_date: Optional[str] = Field(None, alias="LastTradingDate", description="The final day that a futures contract may trade or be closed out before the delivery of the underlying asset or cash settlement must occur.")
    low52_week: Optional[str] = Field(None, alias="Low52Week", description="The lowest price of the past 52 weeks.")
    low52_week_timestamp: Optional[str] = Field(None, alias="Low52WeekTimestamp", description="Date of the lowest price of the past 52 weeks.")
    market_flags: Optional[MarketFlags] = Field(None, alias="MarketFlags")
    net_change: Optional[str] = Field(None, alias="NetChange", description="The difference between the last displayed price and the previous day's close.")
    net_change_pct: Optional[str] = Field(None, alias="NetChangePct", description="The percentage difference between the current price and previous day's close, expressed as a percentage. For example, a price change from 100 to 103.5 would be expressed as `\"3.5\"`.")
    open: Optional[str] = Field(None, alias="Open", description="The opening price of the day.")
    previous_close: Optional[str] = Field(None, alias="PreviousClose", description="The closing price of the previous day.")
    previous_volume: Optional[str] = Field(None, alias="PreviousVolume", description="Daily volume of the previous day.")
    restrictions: Optional[List[str]] = Field(None, alias="Restrictions", description="Restriction if any returns array.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="The name identifying the financial instrument for which the data is displayed.")
    tick_size_tier: Optional[str] = Field(None, alias="TickSizeTier", description="Trading increment based on a level group.")
    trade_time: Optional[str] = Field(None, alias="TradeTime", description="Time of the last trade.")
    volume: Optional[str] = Field(None, alias="Volume", description="Daily volume in shares/contracts.")
    last_size: Optional[str] = Field(None, alias="LastSize", description="Number of contracts/shares last traded.")
    last_venue: Optional[str] = Field(None, alias="LastVenue", description="Exchange name of last trade.")
    vwap: Optional[str] = Field(None, alias="VWAP", description="VWAP (Volume Weighted Average Price) is a measure of the price at which the majority of a given day's trading in a given security took place. It is calculated by adding the dollars traded for the average price of the bar throughout the day (\"avgprice\" x \"number of shares traded\" per bar) and dividing by the total shares traded for the day. The VWAP is calculated throughout the day by the TradeStation data-network.")

class QuoteError(SerializableModel):
    symbol: Optional[str] = Field(None, alias="Symbol", description="The requested symbol.")
    error: Optional[str] = Field(None, alias="Error", description="The Error.")

class QuoteSnapshot(SerializableModel):
    quotes: Optional[List[Quote]] = Field(None, alias="Quotes")
    errors: Optional[List[QuoteError]] = Field(None, alias="Errors")

class QuoteStream(SerializableModel):
    ask: Optional[str] = Field(None, alias="Ask", description="The price at which a security, futures contract, or other financial instrument is offered for sale.")
    ask_size: Optional[str] = Field(None, alias="AskSize", description="The number of trading units that prospective sellers are prepared to sell.")
    bid: Optional[str] = Field(None, alias="Bid", description="The highest price a prospective buyer is prepared to pay at a particular time for a trading unit of a given symbol.")
    bid_size: Optional[str] = Field(None, alias="BidSize", description="The number of trading units that prospective buyers are prepared to purchase for a symbol.")
    close: Optional[str] = Field(None, alias="Close", description="The closing price of the day.")
    daily_open_interest: Optional[str] = Field(None, alias="DailyOpenInterest", description="The total number of open or outstanding (not closed or delivered) options and/or futures contracts that exist on a given day, delivered on a particular day.")
    error: Optional[str] = Field(None, alias="Error", description="Message if there's an error.")
    high: Optional[str] = Field(None, alias="High", description="The highest price of the day.")
    low: Optional[str] = Field(None, alias="Low", description="The lowest price of the day.")
    high52_week: Optional[str] = Field(None, alias="High52Week", description="The highest price of the past 52 weeks.")
    high52_week_timestamp: Optional[str] = Field(None, alias="High52WeekTimestamp", description="Date of the highest price in the past 52 week.")
    last: Optional[str] = Field(None, alias="Last", description="The last price at which the symbol traded.")
    min_price: Optional[str] = Field(None, alias="MinPrice", description="The minimum price a commodity futures contract may be traded for the current session.")
    max_price: Optional[str] = Field(None, alias="MaxPrice", description="The maximum price a commodity futures contract may be traded for the current session.")
    first_notice_date: Optional[str] = Field(None, alias="FirstNoticeDate", description="The day after which an investor who has purchased a futures contract may be required to take physical delivery of the contracts underlying commodity.")
    last_trading_date: Optional[str] = Field(None, alias="LastTradingDate", description="The final day that a futures contract may trade or be closed out before the delivery of the underlying asset or cash settlement must occur.")
    low52_week: Optional[str] = Field(None, alias="Low52Week", description="The lowest price of the past 52 weeks.")
    low52_week_timestamp: Optional[str] = Field(None, alias="Low52WeekTimestamp", description="Date of the lowest price of the past 52 weeks.")
    market_flags: Optional[MarketFlags] = Field(None, alias="MarketFlags")
    net_change: Optional[str] = Field(None, alias="NetChange", description="The difference between the last displayed price and the previous day's close.")
    net_change_pct: Optional[str] = Field(None, alias="NetChangePct", description="The percentage difference between the current price and previous day's close,expressed as a decimal. For example, a price change from 100 to 103.5 would be expressed as `\"0.035\"`.")
    open: Optional[str] = Field(None, alias="Open", description="The opening price of the day.")
    previous_close: Optional[str] = Field(None, alias="PreviousClose", description="The closing price of the previous day.")
    previous_volume: Optional[str] = Field(None, alias="PreviousVolume", description="Daily volume of the previous day.")
    restrictions: Optional[List[str]] = Field(None, alias="Restrictions", description="Restriction if any returns array.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="The name identifying the financial instrument for which the data is displayed.")
    tick_size_tier: Optional[str] = Field(None, alias="TickSizeTier", description="Trading increment based on a level group.")
    trade_time: Optional[str] = Field(None, alias="TradeTime", description="Time of the last trade.")
    volume: Optional[str] = Field(None, alias="Volume", description="Daily volume in shares/contracts.")
    last_size: Optional[str] = Field(None, alias="LastSize", description="Number of contracts/shares last traded.")
    last_venue: Optional[str] = Field(None, alias="LastVenue", description="Exchange name of last trade.")
    vwap: Optional[str] = Field(None, alias="VWAP", description="VWAP (Volume Weighted Average Price) is a measure of the price at which the majority of a given day's trading in a given security took place. It is calculated by adding the dollars traded for the average price of the bar throughout the day (\"avgprice\" x \"number of shares traded\" per bar) and dividing by the total shares traded for the day. The VWAP is calculated throughout the day by the TradeStation data-network.")

class Heartbeat1(SerializableModel):
    heartbeat: Optional[int] = Field(None, alias="Heartbeat", description="The heartbeat, sent to indicate that the stream is alive, although data is not actively being sent. A heartbeat will be sent after 5 seconds on an idle stream.")
    timestamp: Optional[str] = Field(None, alias="Timestamp", description="Timestamp represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard. \nE.g. `2023-01-01T23:30:30Z`.")

class BidQuote(SerializableModel):
    time_stamp: Optional[str] = Field(None, alias="TimeStamp", description="Timestamp of the quote, represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard.  E.g. `2022-06-28T12:34:56Z`.")
    side: Optional[str] = Field(None, alias="Side", description="The `Bid` side of the quote.")
    price: Optional[str] = Field(None, alias="Price", description="The price of the quote.")
    size: Optional[str] = Field(None, alias="Size", description="The total number of shares requested by this participant for the Bid.")
    order_count: Optional[int] = Field(None, alias="OrderCount", description="The number of orders aggregated together for this quote by the participant (market maker or ECN).")
    name: Optional[str] = Field(None, alias="Name", description="The name of the participant associated with this quote.")

class AskQuote(SerializableModel):
    time_stamp: Optional[str] = Field(None, alias="TimeStamp", description="Timestamp of the quote, represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard.  E.g. `2022-06-28T12:34:56Z`.")
    side: Optional[str] = Field(None, alias="Side", description="The `Ask` side of the quote.")
    price: Optional[str] = Field(None, alias="Price", description="The price of the quote.")
    size: Optional[str] = Field(None, alias="Size", description="The total number of shares offered by this participant for the Ask.")
    order_count: Optional[int] = Field(None, alias="OrderCount", description="The number of orders aggregated together for this quote by the participant (market maker or ECN).")
    name: Optional[str] = Field(None, alias="Name", description="The name of the participant associated with this quote.")

class AggregatedBid(SerializableModel):
    earliest_time: Optional[str] = Field(None, alias="EarliestTime", description="The earliest participant timestamp for this quote, represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard.  E.g. `2022-06-28T12:34:01Z`.")
    latest_time: Optional[str] = Field(None, alias="LatestTime", description="The latest participant timestamp for this quote, represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard.  E.g. `2022-06-28T12:34:56Z`.")
    side: Optional[str] = Field(None, alias="Side", description="The `Bid` side of the quote.")
    price: Optional[str] = Field(None, alias="Price", description="The price of the quote.")
    total_size: Optional[str] = Field(None, alias="TotalSize", description="The total number of shares requested by all participants for the Bid.")
    biggest_size: Optional[str] = Field(None, alias="BiggestSize", description="The largest number of shares requested by any participant for the Bid.")
    smallest_size: Optional[str] = Field(None, alias="SmallestSize", description="The smallest number of shares requested by any participant for the Bid.")
    num_participants: Optional[int] = Field(None, alias="NumParticipants", description="The number of participants requesting this Bid price.")
    total_order_count: Optional[int] = Field(None, alias="TotalOrderCount", description="The sum of the order counts for all participants requesting this Bid price.")

class AggregatedAsk(SerializableModel):
    earliest_time: Optional[str] = Field(None, alias="EarliestTime", description="The earliest participant timestamp for this quote, represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard.  E.g. `2022-06-28T12:34:01Z`.")
    latest_time: Optional[str] = Field(None, alias="LatestTime", description="The latest participant timestamp for this quote, represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard.  E.g. `2022-06-28T12:34:56Z`.")
    side: Optional[str] = Field(None, alias="Side", description="The `Ask` side of the quote.")
    price: Optional[str] = Field(None, alias="Price", description="The price of the quote.")
    total_size: Optional[str] = Field(None, alias="TotalSize", description="The total number of shares offered by all participants for the Ask.")
    biggest_size: Optional[str] = Field(None, alias="BiggestSize", description="The largest number of shares offered by any participant for the Ask.")
    smallest_size: Optional[str] = Field(None, alias="SmallestSize", description="The smallest number of shares offered by any participant for the Ask.")
    num_participants: Optional[int] = Field(None, alias="NumParticipants", description="The number of participants offering this Ask price.")
    total_order_count: Optional[int] = Field(None, alias="TotalOrderCount", description="The sum of the order counts for all participants offering this Ask price.")

class MarketDepthQuote(SerializableModel):
    bids: Optional[List[BidQuote]] = Field(None, alias="Bids", description="Contains bid quotes, ordered from high to low price")
    asks: Optional[List[AskQuote]] = Field(None, alias="Asks", description="Contains ask quotes, ordered from low to high price")

class MarketDepthAggregate(SerializableModel):
    bids: Optional[List[AggregatedBid]] = Field(None, alias="Bids", description="Contains aggregated bid quotes, ordered from high to low price")
    asks: Optional[List[AggregatedAsk]] = Field(None, alias="Asks", description="Contains aggregated ask quotes, ordered from low to high price")

class Heartbeat2(SerializableModel):
    heartbeat: Optional[int] = Field(None, alias="Heartbeat", description="The heartbeat, sent to indicate that the stream is alive, although data is not actively being sent. A heartbeat will be sent after 5 seconds on an idle stream.")
    timestamp: Optional[str] = Field(None, alias="Timestamp", description="Timestamp represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard. \nE.g. `2023-01-01T23:30:30Z`.")

class AccountID1(SerializableModel):
    pass

class ErrorResponse1(SerializableModel):
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `BadRequest`, `Unauthorized`, `NotFound`, `Forbidden`, `TooManyRequests`, `InternalServerError`, `NotImplemented`, `ServiceUnavailable`, or `GatewayTimeout`.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")

class StreamOrderErrorResponse(SerializableModel):
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `Forbidden`, `InternalServerError`, `ServiceUnavailable`, `GatewayTimeout`, or `Failed`.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")
    account_id: Optional[str] = Field(None, alias="AccountID", description="The requested Account ID. Returned with the `Forbidden` error type.")

class StreamOrderByOrderIdErrorResponse(SerializableModel):
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `Forbidden`, `InternalServerError`, `ServiceUnavailable`, `GatewayTimeout`, `Failed`, or `NotFound`.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")
    account_id: Optional[str] = Field(None, alias="AccountID", description="The requested Account ID. Returned with the `Forbidden` error type.")
    order_id: Optional[str] = Field(None, alias="OrderID", description="The order ID of this order.")

class StreamPositionsErrorResponse(SerializableModel):
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `Forbidden`, `InternalServerError`, `ServiceUnavailable`, `GatewayTimeout`, or `Failed`.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")
    account_id: Optional[str] = Field(None, alias="AccountID", description="The requested Account ID. Returned with the `Forbidden` error type.")

class MarketActivationRules1(SerializableModel):
    rule_type: Optional[str] = Field(None, alias="RuleType", description="Type of the activation rule. Currently only supports `Price`.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="Symbol that the rule is based on.")
    predicate: Optional[str] = Field(None, alias="Predicate", description="The predicate comparison for the market rule type. E.g. `Lt` (less than).\n- `Lt` - Less Than\n- `Lte` - Less Than or Equal\n- `Gt` - Greater Than\n- `Gte` - Greater Than or Equal")
    trigger_key: Optional[Literal["STT", "STTN", "SBA", "SAB", "DTT", "DTTN", "DBA", "DAB", "TTT", "TTTN", "TBA", "TAB"]] = Field(None, alias="TriggerKey", description="The ticks behavior for the activation rule. Rule descriptions can be obtained from [Get Activation Triggers](#operation/GetActivationTriggers).")
    price: Optional[str] = Field(None, alias="Price", description="Valid only for RuleType=\"Price\", the price at which the rule will trigger when the price hits ticks as specified by TriggerKey.")
    logic_operator: Optional[Literal["And", "Or"]] = Field(None, alias="LogicOperator", description="Relation with the previous activation rule when given a list of MarketActivationRules. Ignored for the first MarketActivationRule.")

class OrderRelationship1(SerializableModel):
    order_id: Optional[str] = Field(None, alias="OrderID", description="The order ID of the linked order.")
    relationship: Optional[str] = Field(None, alias="Relationship", description="Describes the relationship of a linked order within a group order to the current returned order. Valid Values are: `BRK`, `OSP` (linked parent), `OSO` (linked child), and `OCO`.")

class TrailingStop1(SerializableModel):
    amount: Optional[str] = Field(None, alias="Amount", description="Currency Offset from current price. Note: Mutually exclusive with Percent.")
    percent: Optional[str] = Field(None, alias="Percent", description="Percentage offset from current price. Note: Mutually exclusive with Amount.")

class OrderLeg1(SerializableModel):
    asset_type: Optional[Literal["UNKNOWN", "STOCK", "STOCKOPTION", "FUTURE", "FUTUREOPTION", "FOREX", "CURRENCYOPTION", "INDEX", "INDEXOPTION"]] = Field(None, alias="AssetType", description="Indicates the asset type of the order.")
    buy_or_sell: Optional[str] = Field(None, alias="BuyOrSell", description="Identifies whether the order is a buy or sell. Valid values are `Buy`, `Sell`, `SellShort`, or `BuyToCover`.")
    exec_quantity: Optional[str] = Field(None, alias="ExecQuantity", description="Number of shares that have been executed.")
    execution_price: Optional[str] = Field(None, alias="ExecutionPrice", description="The price at which order execution occurred.")
    expiration_date: Optional[dict] = Field(None, alias="ExpirationDate", description="The expiration date of the future or option symbol.")
    open_or_close: Optional[str] = Field(None, alias="OpenOrClose", description="What kind of order leg - Opening or Closing.")
    option_type: Optional[str] = Field(None, alias="OptionType", description="Present for options. Valid values are \"CALL\" and \"PUT\".")
    quantity_ordered: Optional[str] = Field(None, alias="QuantityOrdered", description="Number of shares or contracts being purchased or sold.")
    quantity_remaining: Optional[str] = Field(None, alias="QuantityRemaining", description="In a partially filled order, this is the number of shares or contracts that were unfilled.")
    strike_price: Optional[str] = Field(None, alias="StrikePrice", description="Present for options. The price at which the holder of an options contract can buy or sell the underlying asset.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="Symbol for the leg order.")
    underlying: Optional[str] = Field(None, alias="Underlying", description="Underlying Symbol associated. Only applies to Futures and Options.")

class TimeUtc1(SerializableModel):
    pass

class TimeActivationRules1(SerializableModel):
    time_utc: Optional[TimeUtc1] = Field(None, alias="TimeUtc")

class Status1(SerializableModel):
    pass

class OrderType1(SerializableModel):
    pass

class Order1(SerializableModel):
    account_id: Optional[AccountID1] = Field(None, alias="AccountID")
    advanced_options: Optional[str] = Field(None, alias="AdvancedOptions", description="Will display a value when the order has advanced order rules associated with it or\nis part of a bracket order. Valid Values are: `CND`, `AON`, `TRL`, `SHWQTY`, `DSCPR`, `NON`, `PEGVAL`, `BKO`, `PSO`\n* `AON` - All or None\n* `BKO` - Book Only\n* `CND` - Activation Rule\n* `DSCPR=<Price>` - Discretionary price\n* `NON` - Non-Display\n* `PEGVAL=<Value>` - Peg Value\n* `PSO` - Add Liquidity\n* `SHWQTY=<quantity>` - Show Only\n* `TRL` - Trailing Stop")
    closed_date_time: Optional[str] = Field(None, alias="ClosedDateTime", description="The Closed Date Time of this order.")
    commission_fee: Optional[str] = Field(None, alias="CommissionFee", description="The actual brokerage commission cost and routing fees (if applicable) for a trade based on the number of shares or contracts.")
    conditional_orders: Optional[List[OrderRelationship1]] = Field(None, alias="ConditionalOrders", description="Describes the relationship between linked orders in a group and this order.")
    conversion_rate: Optional[str] = Field(None, alias="ConversionRate", description="Indicates the rate used to convert from the currency of the symbol to the currency of the account. Omits if not set.")
    currency: Optional[str] = Field(None, alias="Currency", description="Currency used to complete the Order.")
    duration: Optional[str] = Field(None, alias="Duration", description="The amount of time for which an order is valid.")
    filled_price: Optional[str] = Field(None, alias="FilledPrice", description="At the top level, this is the average fill price. For expanded levels, this is the actual execution price.")
    good_till_date: Optional[str] = Field(None, alias="GoodTillDate", description="For GTC, GTC+, GTD and GTD+ order durations. The date the order will expire on in UTC format. The time portion, if \"T00:00:00Z\", should be ignored.")
    group_name: Optional[str] = Field(None, alias="GroupName", description="It can be used to identify orders that are part of the same bracket.")
    legs: Optional[List[OrderLeg1]] = Field(None, alias="Legs", description="An array of legs associated with this order.")
    market_activation_rules: Optional[List[MarketActivationRules1]] = Field(None, alias="MarketActivationRules", description="Allows you to specify when an order will be placed based on the price action of one or more symbols.")
    time_activation_rules: Optional[List[TimeActivationRules1]] = Field(None, alias="TimeActivationRules", description="Allows you to specify a time that an order will be placed.")
    limit_price: Optional[str] = Field(None, alias="LimitPrice", description="The limit price for Limit and Stop Limit orders.")
    opened_date_time: Optional[str] = Field(None, alias="OpenedDateTime", description="Time the order was placed.")
    order_id: Optional[str] = Field(None, alias="OrderID", description="The order ID of this order.")
    order_type: Optional[OrderType1] = Field(None, alias="OrderType")
    price_used_for_buying_power: Optional[str] = Field(None, alias="PriceUsedForBuyingPower", description="Price used for the buying power calculation of the order.")
    reject_reason: Optional[str] = Field(None, alias="RejectReason", description="If an order has been rejected, this will display the rejection. reason")
    routing: Optional[str] = Field(None, alias="Routing", description="Identifies the routing selection made by the customer when placing the order.")
    show_only_quantity: Optional[str] = Field(None, alias="ShowOnlyQuantity", description="Hides the true number of shares intended to be bought or sold. Valid for `Limit`, and `StopLimit` order types. Not valid for all exchanges.")
    spread: Optional[str] = Field(None, alias="Spread", description="The spread type for an option order.")
    status: Optional[Status1] = Field(None, alias="Status")
    status_description: Optional[str] = Field(None, alias="StatusDescription", description="Description of the status.")
    stop_price: Optional[str] = Field(None, alias="StopPrice", description="The stop price for StopLimit and StopMarket orders.")
    trailing_stop: Optional[TrailingStop1] = Field(None, alias="TrailingStop")
    unbundled_route_fee: Optional[str] = Field(None, alias="UnbundledRouteFee", description="Only applies to equities.  Will contain a value if the order has received a routing fee.")

class Heartbeat3(SerializableModel):
    heartbeat: Optional[int] = Field(None, alias="Heartbeat", description="The heartbeat, sent to indicate that the stream is alive, although data is not actively being sent. A heartbeat will be sent after 5 seconds on an idle stream.")
    timestamp: Optional[str] = Field(None, alias="Timestamp", description="Timestamp represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard. \nE.g. `2023-01-01T23:30:30Z`.")

class StreamStatus(SerializableModel):
    stream_status: Optional[str] = Field(None, alias="StreamStatus", description="Provides information about the stream status. When the initial snapshot is complete, \"EndSnapshot\" is returned. When the server is about to shut down, \"GoAway\" is returned to indicate that the stream will close because of server shutdown, and that a new stream will need to be started by the client.")

class PositionDirection1(SerializableModel):
    pass

class Position(SerializableModel):
    account_id: Optional[AccountID1] = Field(None, alias="AccountID")
    asset_type: Optional[Literal["STOCK", "STOCKOPTION", "FUTURE", "INDEXOPTION"]] = Field(None, alias="AssetType", description="Indicates the asset type of the position.")
    average_price: Optional[str] = Field(None, alias="AveragePrice", description="The average price of the position currently held.")
    bid: Optional[str] = Field(None, alias="Bid", description="The highest price a prospective buyer is prepared to pay at a particular time for a trading unit of a given symbol.")
    ask: Optional[str] = Field(None, alias="Ask", description="The price at which a security futures contract or other financial instrument is offered for sale.")
    conversion_rate: Optional[str] = Field(None, alias="ConversionRate", description="The currency conversion rate that is used in order to convert from the currency of the symbol to the currency of the account.")
    deleted: Optional[bool] = Field(None, alias="Deleted", description="Indicates that a position has been deleted (i.e., closed) since the last stream update. This property is returned only when the value is true, and only alongside a valid `PositionID` (other properties are omitted).")
    day_trade_requirement: Optional[str] = Field(None, alias="DayTradeRequirement", description="(Futures) DayTradeMargin used on open positions. Currently only calculated for futures positions. Other asset classes will have a 0 for this value.")
    expiration_date: Optional[str] = Field(None, alias="ExpirationDate", description="The UTC formatted expiration date of the future or option symbol in the country the contract is traded in. The time portion of the value should be ignored.")
    initial_requirement: Optional[str] = Field(None, alias="InitialRequirement", description="Only applies to future and option positions. The margin account balance denominated in the symbol currency required for entering a position on margin.")
    maintenance_margin: Optional[str] = Field(None, alias="MaintenanceMargin", description="The margin account balance denominated in the account currency required for maintaining a position on margin.")
    last: Optional[str] = Field(None, alias="Last", description="The last price at which the symbol traded.")
    long_short: Optional[PositionDirection1] = Field(None, alias="LongShort")
    mark_to_market_price: Optional[str] = Field(None, alias="MarkToMarketPrice", description="Only applies to equity and option positions. The MarkToMarketPrice value is the weighted average of the previous close price for the position quantity held overnight and the purchase price of the position quantity opened during the current market session. This value is used to calculate TodaysProfitLoss.")
    market_value: Optional[str] = Field(None, alias="MarketValue", description="The actual market value denominated in the symbol currency of the open position. This value is updated in real-time.")
    position_id: Optional[str] = Field(None, alias="PositionID", description="A unique identifier for the position.")
    quantity: Optional[str] = Field(None, alias="Quantity", description="The number of shares or contracts for a particular position. This value is negative for short positions.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="Symbol of the position.")
    timestamp: Optional[str] = Field(None, alias="Timestamp", description="Time the position was entered.")
    todays_profit_loss: Optional[str] = Field(None, alias="TodaysProfitLoss", description="Only applies to equity and option positions. This value will be included in the payload to convey the unrealized profit or loss denominated in the account currency on the position held calculated using the MarkToMarketPrice.")
    total_cost: Optional[str] = Field(None, alias="TotalCost", description="The total cost denominated in the account currency of the open position.")
    unrealized_profit_loss: Optional[str] = Field(None, alias="UnrealizedProfitLoss", description="The unrealized profit or loss denominated in the symbol currency on the position held calculated based on the average price of the position.")
    unrealized_profit_loss_percent: Optional[str] = Field(None, alias="UnrealizedProfitLossPercent", description="The unrealized profit or loss on the position expressed as a percentage of the initial value of the position.")
    unrealized_profit_loss_qty: Optional[str] = Field(None, alias="UnrealizedProfitLossQty", description="The unrealized profit or loss denominated in the account currency divided by the number of shares contracts or units held.")

class StreamBalancesErrorResponse(SerializableModel):
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `Forbidden`, `InternalServerError`, `ServiceUnavailable`, `GatewayTimeout`, or `Failed`.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")
    account_id: Optional[str] = Field(None, alias="AccountID", description="The requested Account ID. Returned with the `Forbidden` error type.")

class BalanceDetail1(SerializableModel):
    cost_of_positions: Optional[str] = Field(None, alias="CostOfPositions", description="(Equities) The cost used to calculate today's P/L.")
    day_trade_excess: Optional[str] = Field(None, alias="DayTradeExcess", description="(Equities): (Buying Power Available - Buying Power Used) / Buying Power Multiplier. (Futures): (Cash + UnrealizedGains) - Buying Power Used.")
    day_trade_margin: Optional[str] = Field(None, alias="DayTradeMargin", description="(Futures) Money field representing the current total amount of futures day trade margin.")
    day_trade_open_order_margin: Optional[str] = Field(None, alias="DayTradeOpenOrderMargin", description="(Futures) Money field representing the current amount of money reserved for open orders.")
    day_trades: Optional[str] = Field(None, alias="DayTrades", description="(Equities) The number of day trades placed in the account within the previous 4 trading days. A day trade refers to buying then selling or selling short then buying to cover the same security on the same trading day.")
    initial_margin: Optional[str] = Field(None, alias="InitialMargin", description="(Futures) Sum (Initial Margins of all positions in the given account).")
    maintenance_margin: Optional[Any] = Field(None, alias="MaintenanceMargin", description="(Futures) Indicates the value of real-time maintenance margin.")
    maintenance_rate: Optional[str] = Field(None, alias="MaintenanceRate", description="Maintenance Margin Rate.")
    margin_requirement: Optional[str] = Field(None, alias="MarginRequirement", description="(Futures) Indicates the value of real-time account margin requirement.")
    open_order_margin: Optional[str] = Field(None, alias="OpenOrderMargin", description="(Futures) The dollar amount of Open Order Margin for the given futures account.")
    option_buying_power: Optional[str] = Field(None, alias="OptionBuyingPower", description="(Equities) The intraday buying power for options.")
    options_market_value: Optional[str] = Field(None, alias="OptionsMarketValue", description="(Equities) Market value of open positions.")
    overnight_buying_power: Optional[str] = Field(None, alias="OvernightBuyingPower", description="(Equities) Overnight Buying Power (Regulation T) at the start of the trading day.")
    realized_profit_loss: Optional[str] = Field(None, alias="RealizedProfitLoss", description="Indicates the value of real-time account realized profit or loss.")
    required_margin: Optional[str] = Field(None, alias="RequiredMargin", description="(Equities) Total required margin for all held positions.")
    security_on_deposit: Optional[str] = Field(None, alias="SecurityOnDeposit", description="(Futures) The value of special securities that are deposited by the customer with the clearing firm for the sole purpose of increasing purchasing power in their trading account. This number will be reset daily by the account balances clearing file. The entire value of this field will increase purchasing power.")
    today_real_time_trade_equity: Optional[str] = Field(None, alias="TodayRealTimeTradeEquity", description="(Futures) The unrealized P/L for today. Unrealized P/L - BODOpenTradeEquity.")
    trade_equity: Optional[str] = Field(None, alias="TradeEquity", description="(Futures) The dollar amount of unrealized profit and loss for the given futures account. Same value as RealTimeUnrealizedGains.")
    unrealized_profit_loss: Optional[str] = Field(None, alias="UnrealizedProfitLoss", description="Indicates the value of real-time account unrealized profit or loss.")
    unsettled_funds: Optional[str] = Field(None, alias="UnsettledFunds", description="Unsettled Funds are funds that have been closed but not settled.")

class StreamBalance(SerializableModel):
    account_id: Optional[AccountID1] = Field(None, alias="AccountID")
    account_type: Optional[Literal["Cash", "Margin", "Futures", "DVP"]] = Field(None, alias="AccountType", description="The type of the account.")
    balance_detail: Optional[BalanceDetail1] = Field(None, alias="BalanceDetail")
    buying_power: Optional[str] = Field(None, alias="BuyingPower", description="Buying Power available in the account.")
    cash_balance: Optional[str] = Field(None, alias="CashBalance", description="Indicates the value of real-time cash balance.")
    commission: Optional[str] = Field(None, alias="Commission", description="The brokerage commission cost and routing fees (if applicable) for a trade based on the number of shares or contracts.")
    currency_details: Optional[List[CurrencyDetail]] = Field(None, alias="CurrencyDetails", description="Only applies to futures. Collection of properties that describe balance characteristics in different currencies.")
    equity: Optional[str] = Field(None, alias="Equity", description="The real-time equity of the account.")
    market_value: Optional[str] = Field(None, alias="MarketValue", description="Market value of open positions.")
    todays_profit_loss: Optional[str] = Field(None, alias="TodaysProfitLoss", description="Unrealized profit and loss, for the current trading day, of all open positions.")
    uncleared_deposit: Optional[str] = Field(None, alias="UnclearedDeposit", description="The total of uncleared checks received by Tradestation for deposit.")