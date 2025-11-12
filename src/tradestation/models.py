from enum import Enum
from typing import List, Any, Union, Literal, Optional
from pydantic_core import core_schema
from pydantic import BaseModel, RootModel, Field, GetCoreSchemaHandler, ConfigDict
import httpx
from datetime import datetime, time, date, timezone

class SerializableModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,  #  allows using Python field names
    )

    @classmethod
    def from_dict(cls, data: dict):
        return cls.model_validate(data, by_alias=True)

    def to_dict(self):
        return self.model_dump(by_alias=True,exclude_none=True)

class TimeStamp(datetime):
    """Automatically parse str to datetime (Pydantic v2-compatible)."""

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler: GetCoreSchemaHandler):
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def _validate(cls, value: str) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(f"Invalid datetime format: {value}")
        raise TypeError(f"Invalid type for TimeStamp: {type(value)}")

class TimeUtc(time):
    """Timestamp represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard.\nFor time activated orders, the date portion is required but not relevant. E.g. `2023-01-01T23:30:30Z`."""

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler: GetCoreSchemaHandler):
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def _validate(cls, value: str) -> time:
        if isinstance(value, time):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).time()
            except ValueError:
                raise ValueError(f"Invalid datetime format: {value}")
        raise TypeError(f"Invalid type for TimeStamp: {type(value)}")

    @classmethod
    def _serialize(cls, value: time, _info):
        """Serialize as RFC3339 time string with Z for UTC."""
        if value.tzinfo is None:
            # assume UTC if naive
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat().replace("+00:00", "Z")

class DateUtc(date):
    """Timestamp represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard.\nFor time activated orders, the date portion is required but not relevant. E.g. `2023-01-01T23:30:30Z`."""

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler: GetCoreSchemaHandler):
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def _validate(cls, value: str) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).date()
            except ValueError:
                raise ValueError(f"Invalid datetime format: {value}")
        raise TypeError(f"Invalid type for TimeStamp: {type(value)}")

    @classmethod
    def _serialize(cls, value: date, _info):
        """Serialize as RFC3339 time string with Z for UTC."""
        if value.tzinfo is None:
            # assume UTC if naive
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat().replace("+00:00", "Z")

class SymbolSuggestDefinition(SerializableModel):
    category: str = Field(..., alias="Category", description="The type of financial instrument that the symbol represents, such as a stock, index, or mutual fund.")
    country: Literal["US", "United States", "DE", "CA"] = Field(..., alias="Country", description="The country of the exchange where the symbol is listed.")
    currency: Literal["USD", "AUD", "CAD", "CHF", "DKK", "EUR", "DBP", "HKD", "JPY", "NOK", "NZD", "SEK", "SGD"] = Field(..., alias="Currency", description="Displays the type of base currency for the selected symbol.")
    description: str = Field(..., alias="Description", description="Displays the full name of the symbol.")
    display_type: float = Field(..., alias="DisplayType", description="Symbol's price display type based on the following list:\n\n* `0` \"Automatic\" => .00 (should be handled as 2 decimals)\n* `1` 0 Decimals => 1\n* `2` 1 Decimals => .1\n* `3` 2 Decimals => .01\n* `4` 3 Decimals => .001\n* `5` 4 Decimals => .0001\n* `6` 5 Decimals => .00001\n* `7` Simplest Fraction\n* `8` 1/2-Halves => .5\n* `9` 1/4-Fourths => .25\n* `10` 1/8-Eights => .125\n* `11` 1/16-Sixteenths => .0625\n* `12` 1/32-ThirtySeconds => .03125\n* `13` 1/64-SixtyFourths => .015625\n* `14` 1/128-OneTwentyEigths => .0078125\n* `15` 1/256-TwoFiftySixths => .003906250\n* `16` 10ths and Quarters => .025\n* `17` 32nds and Halves => .015625\n* `18` 32nds and Quarters => .0078125\n* `19` 32nds and Eights => .00390625\n* `20` 32nds and Tenths => .003125\n* `21` 64ths and Halves => .0078125\n* `22` 64ths and Tenths => .0015625\n* `23` 6 Decimals => .000001\n")
    error: Optional[str] = Field(..., alias="Error", description="Element that references error.")
    exchange: str = Field(..., alias="Exchange", description="Name of exchange where this symbol is traded in.")
    exchange_id: float = Field(..., alias="ExchangeID", description="A unique numerical identifier for the Exchange.")
    expiration_date: str = Field(..., alias="ExpirationDate", description="Displays the expiration date for a futures or options contract in UTC formatted time.")
    expiration_type: Optional[str] = Field(None, alias="ExpirationType", description="For options only. It indicates whether the option is a monthly, weekly, quarterly or end of month expiration.\n* W - Weekly\n* M - Monthly\n* Q - Quartely\n* E - End of the month\n* \"\" - The term not be identified\n")
    future_type: str = Field(..., alias="FutureType", description="Displays the type of future contract the symbol represents.")
    min_move: float = Field(..., alias="MinMove", description="Multiplying factor using the display type to determine the minimum price increment the asset trades in. For options the MinMove may vary. If the MinMove is negative, then the MinMove is dependent on the price. The whole number portion of the min move is the threshold. The leftmost two digits to the right of the decimal (X.XXXX) indicate the min move beneath the threshold, and the rightmost two digits (X.XXXX) indicate the min move above the threshold.")
    name: str = Field(..., alias="Name", description="A unique series of letters assigned to a security for trading purposes.")
    option_type: str = Field(..., alias="OptionType", description="Displays the type of options contract the symbol represents. Valid options include: Puts, Calls.")
    point_value: float = Field(..., alias="PointValue", description="Symbol`s point value.")
    root: str = Field(..., alias="Root", description="The Symbol root.")
    strike_price: float = Field(..., alias="StrikePrice", description="Displays strike price of an options contract; For Options symbols only.")

class SymbolSuggestDefinitions(RootModel[List[SymbolSuggestDefinition]]):
    """List of suggested symbols based on partial input."""
    pass

class Error(SerializableModel):
    trace_id: Optional[str] = Field(None, alias="TraceId")
    status_code: Optional[int] = Field(None, alias="StatusCode")
    message: Optional[str] = Field(None, alias="Message")

class SymbolSearchDefinition(SerializableModel):
    category: str = Field(..., alias="Category", description="The type of financial instrument that the symbol represents, such as a stock, index, or mutual fund.")
    country: Literal["US", "United States", "DE", "CA"] = Field(..., alias="Country", description="The country of the exchange where the symbol is listed.")
    currency: Literal["USD", "AUD", "CAD", "CHF", "DKK", "EUR", "DBP", "HKD", "JPY", "NOK", "NZD", "SEK", "SGD"] = Field(..., alias="Currency", description="Displays the type of base currency for the selected symbol.")
    description: str = Field(..., alias="Description", description="Displays the full name of the symbol.")
    display_type: float = Field(..., alias="DisplayType", description="Symbol's price display type based on the following list:\n\n* `0` \"Automatic\" Not used\n* `1` 0 Decimals => 1\n* `2` 1 Decimals => .1\n* `3` 2 Decimals => .01\n* `4` 3 Decimals => .001\n* `5` 4 Decimals => .0001\n* `6` 5 Decimals => .00001\n* `7` Simplest Fraction\n* `8` 1/2-Halves => .5\n* `9` 1/4-Fourths => .25\n* `10` 1/8-Eights => .125\n* `11` 1/16-Sixteenths => .0625\n* `12` 1/32-ThirtySeconds => .03125\n* `13` 1/64-SixtyFourths => .015625\n* `14` 1/128-OneTwentyEigths => .0078125\n* `15` 1/256-TwoFiftySixths => .003906250\n* `16` 10ths and Quarters => .025\n* `17` 32nds and Halves => .015625\n* `18` 32nds and Quarters => .0078125\n* `19` 32nds and Eights => .00390625\n* `20` 32nds and Tenths => .003125\n* `21` 64ths and Halves => .0078125\n* `22` 64ths and Tenths => .0015625\n* `23` 6 Decimals => .000001\n")
    error: Optional[str] = Field(..., alias="Error", description="Element that references error.")
    exchange: str = Field(..., alias="Exchange", description="Name of exchange where this symbol is traded in.")
    exchange_id: float = Field(..., alias="ExchangeID", description="A unique numerical identifier for the Exchange.")
    expiration_date: str = Field(..., alias="ExpirationDate", description="Displays the expiration date for a futures or options contract in UTC formatted time.")
    expiration_type: Optional[str] = Field(None, alias="ExpirationType", description="For options only. It indicates whether the option is a monthly, weekly, quarterly or end of month expiration.\n* W - Weekly\n* M - Monthly\n* Q - Quartely\n* E - End of the month\n* \"\" - The term not be identified\n")
    future_type: str = Field(..., alias="FutureType", description="Displays the type of future contract the symbol represents.")
    min_move: float = Field(..., alias="MinMove", description="Multiplying factor using the display type to determine the minimum price increment the asset trades in. For options the MinMove may vary. If the MinMove is negative, then the MinMove is dependent on the price. The whole number portion of the min move is the threshold. The leftmost two digits to the right of the decimal (X.XXXX) indicate the min move beneath the threshold, and the rightmost two digits (X.XXXX) indicate the min move above the threshold.")
    name: str = Field(..., alias="Name", description="A unique series of letters assigned to a security for trading purposes.")
    option_type: str = Field(..., alias="OptionType", description="Displays the type of options contract the symbol represents. Valid options include: Puts, Calls.")
    point_value: float = Field(..., alias="PointValue", description="Symbol`s point value.")
    root: str = Field(..., alias="Root", description="The Symbol root.")
    strike_price: float = Field(..., alias="StrikePrice", description="Displays strike price of an options contract; For Options symbols only.")
    underlying: str = Field(..., alias="Underlying", description="The financial instrument on which an option contract is based or derived.")
class SymbolSearchDefinitions(RootModel[List[SymbolSearchDefinition]]):
    """List of searched symbols based on detailed criteria."""
    pass

class StatusDefinition(SerializableModel):
    """Status value for Barcharts and Tickbars. Integer value represeting values through bit mappings"""
    bit0: Optional[int] = Field(None, alias="bit0", description="`NEW`: Set on the first time the bar is sent")
    bit1: Optional[int] = Field(None, alias="bit1", description="`REAL_TIME_DATA`: Set when there is data in the bar and the data is being built in \"real time\"\" from a trade")
    bit2: Optional[int] = Field(None, alias="bit2", description="`HISTORICAL_DATA`: Set when there is data in the bar and the data is historical data, or is built from historical data")
    bit3: Optional[int] = Field(None, alias="bit3", description="`STANDARD_CLOSE`: Set when the bar is closed \"normally\" (e.g. a 2 tick tickchart bar was closed because of the second tick, a 10-min barchart was closed due to time, etc.)")
    bit4: Optional[int] = Field(None, alias="bit4", description="`END_OF_SESSION_CLOSE`: Set when the bar was closed \"prematurely\" due to the end of the trading session and the particular bar type is not meant to span trading sessions")
    bit5: Optional[int] = Field(None, alias="bit5", description="`UPDATE_CORPACTION`: Set when there was an update due to corporate action")
    bit6: Optional[int] = Field(None, alias="bit6", description="`UPDATE_CORRECTION`: Set when there was an update due to a market correction")
    bit7: Optional[int] = Field(None, alias="bit7", description="`ANALYSIS_BAR`: Set when the bar should not be considered except for analysis purposes")
    bit8: Optional[int] = Field(None, alias="bit8", description="`EXTENDED_BAR`: Set when the bar is linked with an extended transaction linked with the primary stream (i.e. Conversions)")
    bit19: Optional[int] = Field(None, alias="bit19", description="`PREV_DAY_CORRECTION`: Set when there was an update due to prev.day correction")
    bit23: Optional[int] = Field(None, alias="bit23", description="`AFTER_MARKET_CORRECTION`: Set when there was an update due to an after market correction")
    bit24: Optional[int] = Field(None, alias="bit24", description="`PHANTOM_BAR`: Set when the bar is synthetic - thus created only to fill gaps")
    bit25: Optional[int] = Field(None, alias="bit25", description="`EMPTY_BAR`: Set when the bar is an empty bar – no market data for the bar period")
    bit26: Optional[int] = Field(None, alias="bit26", description="`BACKFILL_DATA`: Set when the bar is sent during backfill historical processing")
    bit27: Optional[int] = Field(None, alias="bit27", description="`ARCHIVE_DATA`: Set when the bar is sent during archive historical processing")
    bit28: Optional[int] = Field(None, alias="bit28", description="`GHOST_BAR`: Set when the bar is empty but specifically for the end session")
    bit29: Optional[int] = Field(None, alias="bit29", description="`END_OF_HISTORY_STREAM`: Set on a bar to convey to consumer that all historical bars have been sent.  Historical bars are not guaranteed to be returned in order")

class TickbarDefinition(SerializableModel):
    """Standard tickbar data object for streaming tick bars with stream/tickbars/..."""
    close: Optional[float] = Field(None, alias="Close", description="Close price of current bar.")
    status: Optional[StatusDefinition] = Field(None, alias="Status")
    time_stamp: Optional[str] = Field(None, alias="TimeStamp", description="Epoch timestamp.")
    total_volume: Optional[float] = Field(None, alias="TotalVolume", description="The total volume of shares or contracts.")

AccountID = str

class AccountDetail(SerializableModel):
    """(Equities) Contains detailed information about specific accounts depending on account type."""
    day_trading_qualified: Optional[bool] = Field(None, alias="DayTradingQualified", description="Indicates if the account is qualified to day trade as per compliance suitability in TradeStation. An account that is not Day Trading Qualified is subject to restrictions that will not allow it to become a pattern day trader.")
    enrolled_in_reg_tprogram: Optional[bool] = Field(None, alias="EnrolledInRegTProgram", description="For internal use only.  Identifies whether accounts is enrolled in Reg T program.")
    is_stock_locate_eligible: Optional[bool] = Field(None, alias="IsStockLocateEligible", description="True if this account is stock locate eligible; otherwise, false.")
    option_approval_level: Optional[int] = Field(None, alias="OptionApprovalLevel", description="Valid values are: `0`, `1`, `2`, `3`, `4`, and `5`.\n(Equities) The option approval level will determine what options strategies you will be able to employ in the account. In general terms, the levels are defined as follows:\nLevel 0 - No options trading allowed\nLevel 1 - Writing of Covered Calls, Buying Protective Puts\nLevel 2 - Level 1 + Buying Calls, Buying Puts, Writing Covered Puts\nLevel 3 - level 2+ Stock Option Spreads, Index Option Spreads, Butterfly Spreads, Condor Spreads, Iron Butterfly Spreads, Iron Condor Spreads\nLevel 4 - Level 3 + Writing of Naked Puts (Stock Options)\nLevel 5 - Level 4 + Writing of Naked Puts (Index Options), Writing of Naked Calls (Stock Options), Writing of Naked Calls (Index Options)")
    pattern_day_trader: Optional[bool] = Field(None, alias="PatternDayTrader", description="(Equities) Indicates whether you are considered a pattern day trader. As per FINRA rules, you will be considered a pattern day trader if you trade 4 or more times in 5 business days and your day-trading activities are greater than 6 percent of your total trading activity for that same five-day period. A pattern day trader must maintain a minimum equity of $25,000 on any day that the customer day trades. If the account falls below the $25,000 requirement, the pattern day trader will not be permitted to day trade until the account is restored to the $25,000 minimum equity level.")
    requires_buying_power_warning: Optional[bool] = Field(None, alias="RequiresBuyingPowerWarning", description="For internal use only. Identifies whether account is enrolled in the margin buying power warning program to receive alerts prior to placing an order which would exceed their buying power.")

class Account(SerializableModel):
    """Contains brokerage account information for individual brokerage accounts."""
    account_detail: Optional[AccountDetail] = Field(None, alias="AccountDetail")
    account_id: Optional[AccountID] = Field(None, alias="AccountID")
    account_type: Optional[str] = Field(None, alias="AccountType", description="The type of the TradeStation Account. Valid values are: `Cash`, `Margin`, `Futures`, and `DVP`.")
    alias: Optional[str] = Field(None, alias="Alias", description="A user specified name that identifies a TradeStation account. Omits if not set.")
    alt_id: Optional[str] = Field(None, alias="AltID", description="TradeStation account ID for accounts based in Japan. Omits if not set.")
    currency: Optional[str] = Field(None, alias="Currency", description="Currency associated with this account.")
    status: Optional[str] = Field(None, alias="Status", description="Status of a specific account:\n- Active\n- Closed\n- Closing Transaction Only\n- Margin Call - Closing Transactions Only\n- Inactive\n- Liquidating Transactions Only\n- Restricted\n- 90 Day Restriction-Closing Transaction Only")

class Accounts(SerializableModel):
    """Contains brokerage account information for the identified user."""
    accounts: List[Account] = Field(None, alias="Accounts")

class ErrorResponse(SerializableModel):
    """Contains error details."""
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `BadRequest`, `Unauthorized`, `Forbidden`, `TooManyRequests`, `InternalServerError`, `NotImplemented`, `ServiceUnavailable`, or `GatewayTimeout`.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")

class BalanceError(SerializableModel):
    """balanceError is an object supplied when a partial success response is returned with some errors."""
    account_id: Optional[str] = Field(None, alias="AccountID", description="The AccountID of the error, may contain multiple Account IDs in comma separated format.")
    error: Optional[str] = Field(None, alias="Error", description="The Error.")
    message: Optional[str] = Field(None, alias="Message", description="The error message.")

class BalanceDetail(SerializableModel):
    """Contains real-time balance information that varies according to account type."""
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
    """Contains currency detail information which varies according to account type."""
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
    """Contains realtime balance information for a single account."""
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
    """Contains a collection of realtime balance information."""
    balances: Optional[List[Balance]] = Field(None, alias="Balances")
    errors: Optional[List[BalanceError]] = Field(None, alias="Errors")

class BODCurrencyDetail(SerializableModel):
    """Contains beginning of day currency detail information which varies according to account type."""
    account_margin_requirement: Optional[str] = Field(None, alias="AccountMarginRequirement", description="The dollar amount of Beginning Day Margin for the given forex account.")
    account_open_trade_equity: Optional[str] = Field(None, alias="AccountOpenTradeEquity", description="The dollar amount of Beginning Day Trade Equity for the given account.")
    account_securities: Optional[str] = Field(None, alias="AccountSecurities", description="The value of special securities that are deposited by the customer with the clearing firm for the sole purpose of increasing purchasing power in their trading account. This number will be reset daily by the account balances clearing file. The entire value of this field will increase purchasing power.")
    cash_balance: Optional[str] = Field(None, alias="CashBalance", description="The dollar amount of the Beginning Day Cash Balance for the given account.")
    currency: Optional[str] = Field(None, alias="Currency", description="The currency of the entity.")
    margin_requirement: Optional[str] = Field(None, alias="MarginRequirement", description="The dollar amount of Beginning Day Margin for the given forex account.")
    open_trade_equity: Optional[str] = Field(None, alias="OpenTradeEquity", description="The dollar amount of Beginning Day Trade Equity for the given account.")
    securities: Optional[str] = Field(None, alias="Securities", description="Indicates the dollar amount of Beginning Day Securities")

class BODBalanceDetail(SerializableModel):
    """Contains detailed beginning of day balance information which varies according to account type."""
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
    """Contains beginning of day balance information for a single account."""
    account_id: Optional[AccountID] = Field(None, alias="AccountID")
    account_type: Optional[str] = Field(None, alias="AccountType", description="The account type of this account.")
    balance_detail: Optional[BODBalanceDetail] = Field(None, alias="BalanceDetail")
    currency_details: Optional[List[BODCurrencyDetail]] = Field(None, alias="CurrencyDetails", description="Only applies to futures. Contains beginning of day currency detail information which varies according to account type.")

class BalancesBOD(SerializableModel):
    """Contains a colleciton of beginning of day balance information."""
    bodbalances: Optional[List[BODBalance]] = Field(None, alias="BODBalances")
    errors: Optional[List[BalanceError]] = Field(None, alias="Errors")

class OrderError(SerializableModel):
    """orderError is an object supplied when a partial success response is returned with some errors."""
    account_id: Optional[str] = Field(None, alias="AccountID", description="The AccountID of the error, may contain multiple Account IDs in comma separated format.")
    error: Optional[str] = Field(None, alias="Error", description="The Error.")
    message: Optional[str] = Field(None, alias="Message", description="The error message.")

class TrailingStop(SerializableModel):
    """TrailingStop offset; amount or percent."""
    amount: Optional[str] = Field(None, alias="Amount", description="Currency Offset from current price. Note: Mutually exclusive with Percent.")
    percent: Optional[str] = Field(None, alias="Percent", description="Percentage offset from current price. Note: Mutually exclusive with Amount.")

class Status(str, Enum):
    ACK = "ACK" # Recieved
    BRO = "BRO" # Broken
    CAN = "CAN" # Canceled
    FLL = "FLL" # Filled
    FLP = "FLP" # Partial Fill (UROut)
    FPR = "FPR" # Partial Fill (Alive)
    LAT = "LAT" # Too Late to Cancel
    OPN = "OPN" # Sent
    OUT = "OUT" # UROut
    REJ = "REJ" # Rejected
    UCH = "UCH" # Replaced
    UCN = "UCN" # Cancel Sent
    TSC = "TSC" # Trade Server Canceled
    RJC = "RJC" # Cancel Request Rejected
    DON = "DON" # Queued
    RSN = "RSN" # Replace Sent
    CND = "CND" # Condition Met
    OSO = "OSO" # OSO Order
    SUS = "SUS" # Suspended
    ASS = "ASS"
    BRC = "BRC"
    BRF = "BRF"
    CHG = "CHG"
    COR = "COR"
    DIS = "DIS"
    DOA = "DOA"
    ECN = "ECN"
    EXE = "EXE"
    PLA = "PLA"
    REC = "REC"
    RPD = "RPD"
    STP = "STP"
    STT = "STT"
    EXP = "EXP"
    RJR = "RJR"
    SCN = "SCN"
    OTHER = "OTHER"

class OrderLeg(SerializableModel):
    """OrderLeg is an object returned from WebAPI."""
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

class OrderRelationship(SerializableModel):
    """Describes the relationship between linked orders in a group and this order."""
    order_id: Optional[str] = Field(None, alias="OrderID", description="The order ID of the linked order.")
    relationship: Optional[str] = Field(None, alias="Relationship", description="Describes the relationship of a linked order within a group order to the current returned order. Valid Values are: `BRK`, `OSP` (linked parent), `OSO` (linked child), and `OCO`.")

class OrderType(str, Enum):
    LIMIT = "Limit"
    STOP_MARKET = "StopMarket"
    MARKET = "Market"
    STOP_LIMIT = "StopLimit"

class MarketActivationRules(SerializableModel):
    rule_type: Optional[str] = Field(None, alias="RuleType", description="Type of the activation rule. Currently only supports `Price`.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="Symbol that the rule is based on.")
    predicate: Optional[str] = Field(None, alias="Predicate", description="The predicate comparison for the market rule type. E.g. `Lt` (less than).\n- `Lt` - Less Than\n- `Lte` - Less Than or Equal\n- `Gt` - Greater Than\n- `Gte` - Greater Than or Equal")
    trigger_key: Optional[Literal["STT", "STTN", "SBA", "SAB", "DTT", "DTTN", "DBA", "DAB", "TTT", "TTTN", "TBA", "TAB"]] = Field(None, alias="TriggerKey", description="The ticks behavior for the activation rule. Rule descriptions can be obtained from [Get Activation Triggers](#operation/GetActivationTriggers).")
    price: Optional[str] = Field(None, alias="Price", description="Valid only for RuleType=\"Price\", the price at which the rule will trigger when the price hits ticks as specified by TriggerKey.")
    logic_operator: Optional[Literal["And", "Or"]] = Field(None, alias="LogicOperator", description="Relation with the previous activation rule when given a list of MarketActivationRules. Ignored for the first MarketActivationRule.")

class TimeActivationRules(SerializableModel):
    """Advanced option for an order. The date portion is not used for a Time Activation rule and is returned as \"0001-01-01\"."""
    time_utc: Optional[TimeUtc] = Field(None, alias="TimeUtc")

class OrderBase(SerializableModel):
    """A brokerage order."""
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

class HistoricalOrder(OrderBase):
    status: Optional[Status] = Field(None, alias="Status")
    status_description: Optional[str] = Field(None, alias="StatusDescription", description="Description of the status.")
    stop_price: Optional[str] = Field(None, alias="StopPrice", description="The stop price for StopLimit and StopMarket orders.")
    trailing_stop: Optional[TrailingStop] = Field(None, alias="TrailingStop")
    unbundled_route_fee: Optional[str] = Field(None, alias="UnbundledRouteFee", description="Only applies to equities.  Will contain a value if the order has received a routing fee.")

class HistoricalOrders(SerializableModel):
    """Orders contains a collection of recent or historical orders for the requested account."""
    orders: Optional[List[HistoricalOrder]] = Field(None, alias="Orders")
    errors: Optional[List[OrderError]] = Field(None, alias="Errors")
    next_token: Optional[str] = Field(None, alias="NextToken", description="A token returned with paginated orders which can be used in a subsequent request to retrieve the next page.")

class OrderByIDError(SerializableModel):
    """orderError is an object supplied when a partial success response is returned with some errors."""
    account_id: Optional[str] = Field(None, alias="AccountID", description="The AccountID of the error, may contain multiple Account IDs in comma separated format.")
    order_id: Optional[str] = Field(None, alias="OrderID", description="The OrderID of the error.")
    error: Optional[str] = Field(None, alias="Error", description="The Error.")
    message: Optional[str] = Field(None, alias="Message", description="The error message.")

class HistoricalOrdersById(SerializableModel):
    """Orders contains a collection of recent or historical orders for the requested account."""
    orders: Optional[List[HistoricalOrder]] = Field(None, alias="Orders")
    errors: Optional[List[OrderByIDError]] = Field(None, alias="Errors")

class Order(OrderBase):
    status: Optional[Status] = Field(None, alias="Status")
    status_description: Optional[str] = Field(None, alias="StatusDescription", description="Description of the status.")
    stop_price: Optional[str] = Field(None, alias="StopPrice", description="The stop price for StopLimit and StopMarket orders.")
    trailing_stop: Optional[TrailingStop] = Field(None, alias="TrailingStop")
    unbundled_route_fee: Optional[str] = Field(None, alias="UnbundledRouteFee", description="Only applies to equities.  Will contain a value if the order has received a routing fee.")

class Orders(SerializableModel):
    """Orders contains a collection of recent or historical orders for the requested account."""
    orders: Optional[List[Order]] = Field(None, alias="Orders")
    errors: Optional[List[OrderError]] = Field(None, alias="Errors")
    next_token: Optional[str] = Field(None, alias="NextToken", description="A token returned with paginated orders which can be used in a subsequent request to retrieve the next page.")

class OrdersById(SerializableModel):
    """Orders contains a collection of recent or historical orders for the requested account."""
    orders: Optional[List[Order]] = Field(None, alias="Orders")
    errors: Optional[List[OrderByIDError]] = Field(None, alias="Errors")

class PositionError(SerializableModel):
    """Returned when a partial success response includes some errors."""
    account_id: Optional[str] = Field(None, alias="AccountID", description="The AccountID of the error, may contain multiple Account IDs in comma separated format.")
    error: Optional[str] = Field(None, alias="Error", description="The Error.")
    message: Optional[str] = Field(None, alias="Message", description="The error message.")

class PositionDirection(str, Enum):
    LONG = "Long"
    SHORT = "Short"

class PositionResponse(SerializableModel):
    """Position represents a position that is returned for an Account."""
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
    """The positions for the given account(s)."""
    positions: Optional[List[PositionResponse]] = Field(None, alias="Positions")
    errors: Optional[List[PositionError]] = Field(None, alias="Errors")

class TradeAction(str, Enum):
    """
    TradeAction represents the different trade actions that can be sent to or received from WebAPI.
    Conveys the intent of the trade:

    - `BUY` - equities and futures
    - `SELL` - equities and futures
    - `BUYTOCOVER` - equities
    - `SELLSHORT` - equities
    - `BUYTOOPEN` - options
    - `BUYTOCLOSE` - options
    - `SELLTOOPEN` - options
    - `SELLTOCLOSE` - options
    """

    BUY = "BUY"
    SELL = "SELL"
    BUYTOCOVER = "BUYTOCOVER"
    SELLSHORT = "SELLSHORT"
    BUYTOOPEN = "BUYTOOPEN"
    BUYTOCLOSE = "BUYTOCLOSE"
    SELLTOOPEN = "SELLTOOPEN"
    SELLTOCLOSE = "SELLTOCLOSE"

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

class AdvancedOrderType(str, Enum):
    NORMAL = "NORMAL"
    BRK = "BRK"
    OCO = "OCO"

class OrderRequestOSO(SerializableModel):
    """OrderRequestOSO defines OSOs for placing a trade on WebAPI."""
    orders: List["OrderRequest"] = Field(..., alias="Orders")
    type: AdvancedOrderType = Field(..., alias="Type")

class OrderRequestLegs(SerializableModel):
    """The legs of an order being submitted."""
    quantity: str = Field(..., alias="Quantity", description="The quantity of the order.")
    symbol: str = Field(..., alias="Symbol", description="The symbol used for this leg of the order.")
    trade_action: TradeAction = Field(..., alias="TradeAction")

class Duration(str, Enum):
    """The length of time for which an order will remain valid in the market. Available values are: DAY, DYP, GTC, GCP, GTD, GDP, OPG, CLO, IOC, FOK, 1, 3, and 5. Different asset classes and routes may have restrictions on the durations they accept.\n* DAY - Day, valid until the end of the regular trading session.\n* DYP - Day Plus; valid until the end of the extended trading session.\n* GTC - Good till canceled. Maximum lifespan is 90 calendar days.\n* GCP - Good till canceled plus. Maximum lifespan is 90 calendar days.\n* GTD - Good through date. Maximum lifespan is 90 calendar days.\n* GDP - Good through date plus. Maximum lifespan is 90 calendar days.\n* OPG - At the opening; only valid for listed stocks at the opening session Price.\n* CLO - On Close; orders that target the closing session of an exchange.\n* IOC - Immediate or Cancel; filled immediately or canceled, partial fills are accepted.\n* FOK - Fill or Kill; orders are filled entirely or canceled, partial fills are not accepted.\n* 1 - 1 minute; expires after the 1 minute. Only valid for equity orders.\n* 3 - 3 minutes; expires after the 3 minutes. Only valid for equity orders.\n* 5 - 5 minutes; expires after the 5 minutes. Only valid for equity orders.\n"""
    DAY = "DAY"   # Day, valid until the end of the regular trading session
    DYP = "DYP"   # Day Plus; valid until the end of the extended trading session
    GTC = "GTC"   # Good till canceled. Maximum lifespan is 90 calendar days
    GCP = "GCP"   # Good till canceled plus. Maximum lifespan is 90 calendar days
    GTD = "GTD"   # Good through date. Maximum lifespan is 90 calendar days
    GDP = "GDP"   # Good through date plus. Maximum lifespan is 90 calendar days
    OPG = "OPG"   # At the opening; only valid for listed stocks at the opening session Price
    CLO = "CLO"   # On Close; orders that target the closing session of an exchange
    IOC = "IOC"   # Immediate or Cancel; filled immediately or canceled, partial fills are accepted
    FOK = "FOK"   # Fill or Kill; orders are filled entirely or canceled, partial fills are not accepted
    MIN_1 = "1"  # 1 minute; expires after 1 minute, only valid for equity orders
    MIN_3 = "3"  # 3 minutes; expires after 3 minutes, only valid for equity orders
    MIN_5 = "5"  # 5 minutes; expires after 5 minutes, only valid for equity orders

class Expiration(SerializableModel):
    """Timestamp represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard.\nOnly applicable to GTD and GDP orders. The full timestamp is required, but only the date portion is relevant. E.g. `2023-01-01T23:30:30Z`."""
    pass

class TimeInForceRequest(SerializableModel):
    """TimeInForce defines the duration and expiration timestamp."""
    duration: Duration = Field(..., alias="Duration", )
    expiration: Optional[DateUtc] = Field(None, alias="Expiration")

class OrderRequest(SerializableModel):
    """Submits 1 or more orders."""
    account_id: AccountID = Field(..., alias="AccountID")
    order_type: OrderType = Field(..., alias="OrderType")
    symbol: str = Field(..., alias="Symbol", description="The symbol used for this order.")
    quantity: str = Field(..., alias="Quantity", description="The quantity of the order.")
    trade_action: TradeAction = Field(..., alias="TradeAction")
    time_in_force: TimeInForceRequest = Field(..., alias="TimeInForce")
    advanced_options: Optional[AdvancedOptions] = Field(None, alias="AdvancedOptions")
    buying_power_warning: Optional[str] = Field(None, alias="BuyingPowerWarning", description="For internal use only. For TradeStation Margin accounts enrolled in the Reg-T program, clients should send\nconfirmation that the customer has been shown appropriate buying power warnings in advance of placing an order\nthat could potentially violate the account's buying power. Valid values are: `Enforce`, `Preconfirmed`, and\n`Confirmed`.")
    legs: Optional[List[OrderRequestLegs]] = Field(None, alias="Legs")
    limit_price: Optional[str] = Field(None, alias="LimitPrice", description="The limit price for this order.")
    osos: Optional[List[OrderRequestOSO]] = Field(None, alias="OSOs")
    order_confirm_id: Optional[str] = Field(None, alias="OrderConfirmID", description="A unique identifier regarding an order used to prevent duplicates. Must be unique per API key, per order, per user.")
    route: Optional[str] = Field('Intelligent', alias="Route", description="The route of the order. For Stocks and Options, Route value will default to `Intelligent` if no value is set. Routes can be obtained from [Get Routes](#operation/Routes).")
    stop_price: Optional[str] = Field(None, alias="StopPrice", description="The stop price for this order. If a TrailingStop amount or percent is passed in with the request (in the AdvancedOptions), and a StopPrice value is also passed in, the StopPrice value is ignored.")

class ExpirationDate(SerializableModel):
    """Timestamp represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard. \nE.g. `2023-01-01T23:30:30Z`."""
    pass

class CallPut(SerializableModel):
    """Defines whether an option is a call or a put. Valid values are `CALL` and `PUT`."""
    pass

class OrderConfirmResponseLeg(SerializableModel):
    """An object that is returned from order confirm in WebAPI."""
    expiration_date: Optional[ExpirationDate] = Field(None, alias="ExpirationDate")
    option_type: Optional[CallPut] = Field(None, alias="OptionType")
    quantity: Optional[str] = Field(None, alias="Quantity", description="The quantity.")
    strike_price: Optional[str] = Field(None, alias="StrikePrice", description="The strike price for this option.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="The symbol name associated with this option.")
    trade_action: Optional[TradeAction] = Field(None, alias="TradeAction")

class OrderConfirmResponse(SerializableModel):
    """The response will also contain asset-specific fields."""
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
    """A collection of OrderConfirmResponse objects."""
    confirmations: List[OrderConfirmResponse] = Field(None, alias="Confirmations")

class GroupOrderRequest(SerializableModel):
    """The request for placing a group trade."""
    orders: List["OrderRequest"] = Field(..., alias="Orders")
    type: str = Field(..., alias="Type", description="The group order type.  Valid values are: `BRK`, `OCO`, and `NORMAL`.")

class OrderResponse(SerializableModel):
    """OrderResponse is the response from placing a trade (OrderRequest)."""
    error: Optional[str] = Field(None, alias="Error")
    message: Optional[str] = Field(None, alias="Message")
    order_id: Optional[str] = Field(None, alias="OrderID")

class OrderResponses(SerializableModel):
    """OrderResponses is an array of OrderResponse objects."""
    errors: Optional[List[OrderResponse]] = Field(None, alias="Errors")
    orders: Optional[List[OrderResponse]] = Field(None, alias="Orders")

class MarketActivationRulesReplace(SerializableModel):
    """Any existing Market Activation Rules will be replaced by the values sent in `Rules`."""
    clear_all: Optional[bool] = Field(None, alias="ClearAll", description="If 'True', removes all activation rules when replacing the order and ignores any rules sent in `Rules`.")
    rules: Optional[List[MarketActivationRules]] = Field(None, alias="Rules")

class TimeActivationRulesReplace(SerializableModel):
    """Advanced option for an order. The date portion is not used for a Time Activation rule and is returned as \"0001-01-01\"."""
    clear_all: Optional[bool] = Field(None, alias="ClearAll", description="If 'True', removes all activation rules when replacing the order and ignores any rules sent in `Rules`.")
    rules: Optional[List[TimeActivationRules]] = Field(None, alias="Rules")

class AdvancedOptionsReplace(SerializableModel):
    show_only_quantity: Optional[str] = Field(None, alias="ShowOnlyQuantity", description="Hides the true number of shares intended to be bought or sold. Valid for `Limit` and `StopLimit` order types. Not valid for all exchanges. For Equities and Futures.")
    trailing_stop: Optional[TrailingStop] = Field(None, alias="TrailingStop")
    market_activation_rules: Optional[MarketActivationRulesReplace] = Field(None, alias="MarketActivationRules", description="Allows you to specify when an order will be placed based on the price action of one or more symbols.")
    time_activation_rules: Optional[TimeActivationRulesReplace] = Field(None, alias="TimeActivationRules", description="Allows you to specify a time that an order will be placed.")

class OrderReplaceRequest(SerializableModel):
    """Describes the order properties which are being updated. Requires at least one updated property."""
    limit_price: Optional[str] = Field(None, alias="LimitPrice", description="The limit price for this order.")
    stop_price: Optional[str] = Field(None, alias="StopPrice", description="The stop price for this order. If a TrailingStop amount or percent is passed in with the request (in the AdvancedOptions), and a StopPrice value is also passed in, the StopPrice value is ignored.")
    order_type: Optional[str] = Field(None, alias="OrderType", description="The order type of this order. Order type can only be updated to `Market`.")
    quantity: Optional[str] = Field(None, alias="Quantity", description="The quantity of this order.")
    advanced_options: Optional[AdvancedOptionsReplace] = Field(None, alias="AdvancedOptions")

class Bar(SerializableModel):
    """Barchart data, starting from a starting date. Each bar filling quantity of unit."""
    close: float = Field(None, alias="Close", description="The close price of the current bar.")
    down_ticks: Optional[int] = Field(None, alias="DownTicks", description="A trade made at a price less than the previous trade price or at a price equal to the previous trade price.")
    down_volume: Optional[int] = Field(None, alias="DownVolume", description="Volume traded on downticks. A tick is considered a downtick if the previous tick was a downtick or the price is lower than the previous tick.")
    epoch: Optional[int] = Field(None, alias="Epoch", description="The Epoch time.")
    high: float = Field(None, alias="High", description="The high price of the current bar.")
    is_end_of_history: Optional[bool] = Field(None, alias="IsEndOfHistory", description="Conveys that all historical bars in the request have been delivered.")
    is_realtime: Optional[bool] = Field(None, alias="IsRealtime", description="Set when there is data in the bar and the data is being built in \"real time\" from a trade.")
    low: float = Field(None, alias="Low", description="The low price of the current bar.")
    open: float = Field(None, alias="Open", description="The open price of the current bar.")
    open_interest: Optional[int] = Field(None, alias="OpenInterest", description="For Options or Futures only. Number of open contracts.")
    time_stamp: Optional[TimeStamp] = Field(None, alias="TimeStamp")
    total_ticks: Optional[int] = Field(None, alias="TotalTicks", description="Total number of ticks (upticks and downticks together).")
    total_volume: Optional[int] = Field(None, alias="TotalVolume", description="The sum of up volume and down volume.")
    unchanged_ticks: Optional[int] = Field(None, alias="UnchangedTicks", description="This field is deprecated, and its value will always be zero.")
    unchanged_volume: Optional[int] = Field(None, alias="UnchangedVolume", description="This field is deprecated, and its value will always be zero.")
    up_ticks: Optional[int] = Field(None, alias="UpTicks", description="A trade made at a price greater than the previous trade price, or at a price equal to the previous trade price.")
    up_volume: Optional[int] = Field(None, alias="UpVolume", description="Volume traded on upticks. A tick is considered an uptick if the previous tick was an uptick or the price is higher than the previous tick.")
    bar_status: Literal["Closed", "Open"] = Field(None, alias="BarStatus", description="Indicates if bar is Open or Closed.")

class Bars(SerializableModel):
    """Contains a list of barchart data."""
    bars: Optional[List[Bar]] = Field(None, alias="Bars")

class Heartbeat(SerializableModel):
    heartbeat: Optional[int] = Field(None, alias="Heartbeat", description="The heartbeat, sent to indicate that the stream is alive, although data is not actively being sent. A heartbeat will be sent after 5 seconds on an idle stream.")
    timestamp: Optional[str] = Field(None, alias="Timestamp", description="Timestamp represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard. \nE.g. `2023-01-01T23:30:30Z`.")

class StreamErrorResponse(SerializableModel):
    """Contains error details."""
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `BadRequest`, `DualLogon`, `GoAway` or `InternalServerError`. When the server is about to shut down, \"GoAway\" is returned to indicate that the stream will close because of server shutdown, and that a new stream will need to be started by the client.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")

class SymbolNames(SerializableModel):
    """A collection of Symbol names."""
    symbol_names: Optional[List[str]] = Field(None, alias="SymbolNames")

class IncrementScheduleRow(SerializableModel):
    """IncrementScheduleRow describes a threshold where prices above or equal to the StartsAt threshold will increment at the\nIncrement value defined. A series of rows are provided to build a table to the IncrementSchedule() scheme option."""
    increment: Optional[str] = Field(None, alias="Increment", description="The incremental value.")
    starts_at: Optional[str] = Field(None, alias="StartsAt", description="The initial value to start incrementing from.")

class PriceFormat(SerializableModel):
    """Conveys number formatting information for symbol price fields."""
    format: Optional[Literal["Decimal", "Fraction", "SubFraction"]] = Field(None, alias="Format", description="The format of the price.")
    decimals: Optional[str] = Field(None, alias="Decimals", description="The number of decimals precision, applies to the `Decimal` format only.")
    fraction: Optional[str] = Field(None, alias="Fraction", description="The denominator of the single fraction, i.e. `1/Fraction`, applies to the `Fraction` format only.")
    sub_fraction: Optional[str] = Field(None, alias="SubFraction", description="The additional fraction of a fraction denominator, applies to the `SubFraction` format only.")
    increment_style: Optional[Literal["Simple", "Schedule"]] = Field(None, alias="IncrementStyle", description="The style of increment for price movements.")
    increment: Optional[str] = Field(None, alias="Increment", description="The decimal increment for all price movements, applies to the `Simple` Increment Style only.")
    increment_schedule: Optional[List[IncrementScheduleRow]] = Field(None, alias="IncrementSchedule")
    point_value: Optional[str] = Field(None, alias="PointValue", description="The symbol's point value.")

class QuantityFormat(SerializableModel):
    """Conveys number formatting information for symbol quantity fields."""
    format: Optional[Literal["Decimal"]] = Field(None, alias="Format", description="The format of the quantity.")
    decimals: Optional[str] = Field(None, alias="Decimals", description="The number of decimals precision, applies to the `Decimal` format only.")
    increment_style: Optional[str] = Field(None, alias="IncrementStyle", description="The incremental style. Valid values are: `Simple` and `Schedule`.")
    increment: Optional[str] = Field(None, alias="Increment", description="The decimal increment for all quantity movements, applies to the `Simple` Increment Style only.")
    increment_schedule: Optional[List[IncrementScheduleRow]] = Field(None, alias="IncrementSchedule")
    minimum_trade_quantity: Optional[str] = Field(None, alias="MinimumTradeQuantity", description="The minimum quantity of an asset that can be traded.")

class AssetType(str, Enum):
    UNKNOWN = "UNKNOWN"
    STOCK = "STOCK"
    STOCKOPTION = "STOCKOPTION"
    FUTURE = "FUTURE"
    FUTUREOPTION = "FUTUREOPTION"
    FOREX = "FOREX"
    CURRENCYOPTION = "CURRENCYOPTION"
    INDEX = "INDEX"
    INDEXOPTION = "INDEXOPTION"
    MUTUALFUND = "MUTUALFUND"
    MONEYMARKETFUND = "MONEYMARKETFUND"
    BOND = "BOND"

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
    """Returned when a partial success response includes some errors."""
    error: Optional[str] = Field(None, alias="Error", description="The Error.")
    message: Optional[str] = Field(None, alias="Message", description="The error message.")
    symbol: Optional[str] = Field(None, alias="Symbol", description="The requested symbol.")

class SymbolDetailsResponse(SerializableModel):
    errors: Optional[List[SymbolDetailsErrorResponse]] = Field(None, alias="Errors")
    symbols: Optional[List[SymbolDetail]] = Field(None, alias="Symbols")

class ActivationTrigger(SerializableModel):
    """The trigger type allows you to specify the type of tick, number, and pattern of ticks that will trigger a specific row of an activation rule."""
    key: Optional[str] = Field(None, alias="Key", description="Value used in the `TriggerKey` property of `MarketActivationRules` in the `AdvancedOptions` for an order. Valid Values are: `STT`, `STTN`, `SBA`, `SAB`, `DTT`, `DTTN`, `DBA`, `DAB`, `TTT`, `TTTN`, `TBA`, and `TAB`.")
    name: Optional[str] = Field(None, alias="Name")
    description: Optional[str] = Field(None, alias="Description")

class ActivationTriggers(SerializableModel):
    """The trigger type allows you to specify the type of tick, number, and pattern of ticks that will trigger a specific row of an activation rule."""
    activation_triggers: Optional[List[ActivationTrigger]] = Field(None, alias="ActivationTriggers")

class Routes(SerializableModel):
    id: Optional[str] = Field(None, alias="Id", description="The ID that must be sent in the optional Route property of a POST order request, when specifying a route for an order.")
    name: Optional[str] = Field(None, alias="Name", description="The name of the route.")
    asset_types: Optional[List[str]] = Field(None, alias="AssetTypes", description="The asset type of the route. Valid Values are: `STOCK`, `FUTURE`, `STOCKOPTION`, and `INDEXOPTION`.")

class OptionExpiration(SerializableModel):
    """Provides information about an option contract expiration."""
    date: Optional[str] = Field(None, alias="Date", description="Timestamp represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard. E.g. `2021-12-17T00:00:00Z`.")
    type: Optional[str] = Field(None, alias="Type", description="Expiration Type, e.g. `Weekly`, `Monthly`, `Quarterly`, `EOM`, or `Other`.")

class Expirations(SerializableModel):
    """Provides the available contract expiration dates for an underlying security."""
    expirations: Optional[List[OptionExpiration]] = Field(None, alias="Expirations")

class RiskRewardAnalysisInputLeg(SerializableModel):
    """Provides information about one leg of a potential option spread trade."""
    symbol: str = Field(..., alias="Symbol", description="Option contract symbol or underlying symbol to be traded for this leg.")
    quantity: int = Field(..., alias="Quantity", description="The number of option contracts to buy or sell for this leg. The value cannot be zero.")
    trade_action: Literal["BUY", "SELL"] = Field(..., alias="TradeAction", description="The kind of trade to place for this leg. Value values are `BUY` and `SELL`.")

class RiskRewardAnalysisInput(SerializableModel):
    """Provides the required information to analyze the risk vs. reward of a potential option spread trade."""
    spread_price: Optional[float] = Field(None, alias="SpreadPrice", description="The quoted price for the option spread trade.")
    legs: Optional[List[RiskRewardAnalysisInputLeg]] = Field(None, alias="Legs", description="The legs of the option spread trade. If more than one leg is specified, the expiration dates must all be the same. In addition, leg symbols must be of type stock, stock option, or index option.")

class RiskRewardAnalysisResult(SerializableModel):
    max_gain_is_infinite: Optional[bool] = Field(None, alias="MaxGainIsInfinite", description="Indicates whether the maximum gain can be infinite.")
    adjusted_max_gain: Optional[str] = Field(None, alias="AdjustedMaxGain", description="The adjusted maximum gain (if it is not infinite).")
    max_loss_is_infinite: Optional[bool] = Field(None, alias="MaxLossIsInfinite", description="Indicates whether the maximum loss can be infinite.")
    adjusted_max_loss: Optional[str] = Field(None, alias="AdjustedMaxLoss", description="The adjusted maximum loss (if it is not infinite).")
    breakeven_points: Optional[List[str]] = Field(None, alias="BreakevenPoints", description="Market price that the underlying security must reach for the trade to avoid a loss.")

class SpreadLeg(SerializableModel):
    """Provides information about one leg of the option spread."""
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
    """Provides information about a specific spread type."""
    name: Optional[str] = Field(None, alias="Name", description="Name of the spread type.")
    strike_interval: Optional[bool] = Field(None, alias="StrikeInterval", description="A true value indicates the spread type is comprised of multiple strike prices. If this is the case, the `strikeInterval` parameter can be used with the [Get Option Chain](#operation/GetOptionChain) and [Get Option Strikes](#operation/GetOptionStrikes) endpoints to specify the interval between the strikes of a spread.")
    expiration_interval: Optional[bool] = Field(None, alias="ExpirationInterval", description="Indicates whether this spread type uses multiple expirations.")

class SpreadTypes(SerializableModel):
    """Provides a list of the available spread types."""
    spread_types: Optional[List[SpreadType]] = Field(None, alias="SpreadTypes")

class Strikes(SerializableModel):
    """Provides a list of the available strikes for a specific spread type."""
    spread_type: Optional[str] = Field(None, alias="SpreadType", description="Name of the spread type for these strikes.")
    strikes: Optional[List[List[str]]] = Field(None, alias="Strikes", description="Array of the strike prices for this spread type. Each element in the Strikes array is an array of strike prices for a single spread.")

class MarketFlags(SerializableModel):
    """Market specific information for a symbol."""
    is_bats: Optional[bool] = Field(None, alias="IsBats", description="Is Bats.")
    is_delayed: Optional[bool] = Field(None, alias="IsDelayed", description="Is delayed.")
    is_halted: Optional[bool] = Field(None, alias="IsHalted", description="Is halted.")
    is_hard_to_borrow: Optional[bool] = Field(None, alias="IsHardToBorrow", description="Is hard to borrow.")

class Quote(SerializableModel):
    """Quote returns current price data for a symbol."""
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
    """Returned when a partial success response includes some errors."""
    symbol: Optional[str] = Field(None, alias="Symbol", description="The requested symbol.")
    error: Optional[str] = Field(None, alias="Error", description="The Error.")

class QuoteSnapshot(SerializableModel):
    """The full snapshot of the latest quote"""
    quotes: Optional[List[Quote]] = Field(None, alias="Quotes")
    errors: Optional[List[QuoteError]] = Field(None, alias="Errors")

class QuoteStream(SerializableModel):
    """Quote returns current price data for a symbol."""
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
    """Contains a single market depth quote for a price, side, and participant."""
    bids: Optional[List[BidQuote]] = Field(None, alias="Bids", description="Contains bid quotes, ordered from high to low price")
    asks: Optional[List[AskQuote]] = Field(None, alias="Asks", description="Contains ask quotes, ordered from low to high price")

class MarketDepthAggregate(SerializableModel):
    """Contains an aggregated market depth quote. Each aggregated quote summarizes the participants for that price and side."""
    bids: Optional[List[AggregatedBid]] = Field(None, alias="Bids", description="Contains aggregated bid quotes, ordered from high to low price")
    asks: Optional[List[AggregatedAsk]] = Field(None, alias="Asks", description="Contains aggregated ask quotes, ordered from low to high price")

class Heartbeat2(SerializableModel):
    heartbeat: Optional[int] = Field(None, alias="Heartbeat", description="The heartbeat, sent to indicate that the stream is alive, although data is not actively being sent. A heartbeat will be sent after 5 seconds on an idle stream.")
    timestamp: Optional[str] = Field(None, alias="Timestamp", description="Timestamp represented as an RFC3339 formatted date, a profile of the ISO 8601 date standard. \nE.g. `2023-01-01T23:30:30Z`.")

class AccountID1(SerializableModel):
    """TradeStation Account ID."""
    pass

class ErrorResponse1(SerializableModel):
    """Contains error details."""
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `BadRequest`, `Unauthorized`, `NotFound`, `Forbidden`, `TooManyRequests`, `InternalServerError`, `NotImplemented`, `ServiceUnavailable`, or `GatewayTimeout`.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")

class StreamOrderErrorResponse(SerializableModel):
    """Contains error details."""
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `Forbidden`, `InternalServerError`, `ServiceUnavailable`, `GatewayTimeout`, or `Failed`.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")
    account_id: Optional[str] = Field(None, alias="AccountID", description="The requested Account ID. Returned with the `Forbidden` error type.")

class StreamOrderByOrderIdErrorResponse(SerializableModel):
    """Contains error details."""
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `Forbidden`, `InternalServerError`, `ServiceUnavailable`, `GatewayTimeout`, `Failed`, or `NotFound`.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")
    account_id: Optional[str] = Field(None, alias="AccountID", description="The requested Account ID. Returned with the `Forbidden` error type.")
    order_id: Optional[str] = Field(None, alias="OrderID", description="The order ID of this order.")

class StreamPositionsErrorResponse(SerializableModel):
    """Contains error details."""
    error: Optional[str] = Field(None, alias="Error", description="Error Title, can be any of `Forbidden`, `InternalServerError`, `ServiceUnavailable`, `GatewayTimeout`, or `Failed`.")
    message: Optional[str] = Field(None, alias="Message", description="The description of the error.")
    account_id: Optional[str] = Field(None, alias="AccountID", description="The requested Account ID. Returned with the `Forbidden` error type.")

class OrderRelationship1(SerializableModel):
    """Describes the relationship between linked orders in a group and this order."""
    order_id: Optional[str] = Field(None, alias="OrderID", description="The order ID of the linked order.")
    relationship: Optional[str] = Field(None, alias="Relationship", description="Describes the relationship of a linked order within a group order to the current returned order. Valid Values are: `BRK`, `OSP` (linked parent), `OSO` (linked child), and `OCO`.")

class OrderType1(str, Enum):
    LIMIT = "Limit"
    STOP_MARKET = "StopMarket"
    MARKET = "Market"
    STOP_LIMIT = "StopLimit"

class Status1(str, Enum):
    ACK = "ACK"
    BRO = "BRO"
    CAN = "CAN"
    EXP = "EXP"
    FLL = "FLL"
    FLP = "FLP"
    FPR = "FPR"
    LAT = "LAT"
    OPN = "OPN"
    OUT = "OUT"
    REJ = "REJ"
    UCH = "UCH"
    UCN = "UCN"
    TSC = "TSC"
    RJC = "RJC"
    DON = "DON"
    RSN = "RSN"
    CND = "CND"
    OSO = "OSO"
    SUS = "SUS"

class StreamStatus(SerializableModel):
    stream_status: str = Field(None, alias="StreamStatus", description="Provides information about the stream status. When the initial snapshot is complete, \"EndSnapshot\" is returned. When the server is about to shut down, \"GoAway\" is returned to indicate that the stream will close because of server shutdown, and that a new stream will need to be started by the client.")

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
    long_short: Optional[PositionDirection] = Field(None, alias="LongShort")
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
