from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union, Literal, get_origin, get_args
from datetime import datetime, timezone
import re

def to_camel_case(snake_str: str) -> str:
    parts = snake_str.split('_')
    return parts[0].capitalize() + ''.join(word.capitalize() for word in parts[1:])

def from_camel_case(camel_str: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()

class SerializableMixin(BaseModel):
    def to_dict(self) -> dict:
        result = {}
        for name, model_field in self.__class__.model_fields.items():
            value = getattr(self, name)
            if value is None:
                continue
            key = to_camel_case(name)
            if isinstance(value, list):
                result[key] = [v.to_dict() if isinstance(v, SerializableMixin) else v for v in value]
            elif isinstance(value, SerializableMixin):
                result[key] = value.to_dict()
            elif isinstance(value, datetime):
                result[key] = value.replace(microsecond=0).astimezone(timezone.utc).isoformat()
            elif isinstance(value, (int, float)):
                result[key] = str(value)
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: dict):
        kwargs = {}
        for name, model_field in cls.model_fields.items():
            key = to_camel_case(name)
            if key not in data:
                continue
            value = data[key]
            annotation = model_field.annotation
            origin = get_origin(annotation)
            args = get_args(annotation)

            if isinstance(annotation, type) and issubclass(annotation, SerializableMixin):
                value = annotation.from_dict(value)
            elif isinstance(annotation, datetime):
                value = datetime.fromisoformat(value)
            elif getattr(annotation, '__origin__', None) is list and hasattr(annotation.__args__[0], 'from_dict'):
                value = [annotation.__args__[0].from_dict(v) for v in value]
            elif origin is Union:
                for arg in args:
                    try:
                        if arg is type(None):
                            continue  # Skip NoneType, already handled
                        if issubclass(arg, SerializableMixin):
                            value = arg.from_dict(value)
                        elif arg is datetime:
                            value = datetime.fromisoformat(value)
                        elif get_origin(arg) is list and hasattr(arg.__args__[0], 'from_dict'):
                            value = [arg.__args__[0].from_dict(v) for v in value]
                        break  # If successful, stop
                    except Exception:
                        continue  # Try next type
            else:
                if isinstance(value, dict):
                    print(f"Warning: {key} is a dict, but expected {annotation}. This may lead to issues.")
            kwargs[name] = value
        return cls(**kwargs)

TradeAction = Literal["BUY", "SELL", "BUYTOCOVER", "SELLSHORT",
                      "BUYTOOPEN", "BUYTOCLOSE", "SELLTOOPEN", "SELLTOCLOSE"]
OrderType = Literal["Limit", "StopMarket", "Market", "StopLimit"]

class TrailingStop(SerializableMixin):
    amount: Optional[float] = None  # Currency offset
    percent: Optional[float] = None  # Percentage offset

class OrderRelationship(SerializableMixin):
    order_ID: str
    relationship: Literal["BRK", "OSP", "OSO", "OCO"]

class OrderLeg(SerializableMixin):
    asset_type: Literal["UNKNOWN", "STOCK", "STOCKOPTION", "FUTURE", "FUTUREOPTION", "FOREX", "CURRENCYOPTION", "INDEX", "INDEXOPTION"]
    symbol: str
    buy_or_sell: Literal['Buy', 'Sell', 'SellShort', 'BuyToCover']
    open_or_close: Literal['Open', 'Close']
    quantity_ordered: int
    exec_quantity: int
    quantity_remaining: int
    execution_price: Optional[float] = None
    expiration_date: Optional[datetime] = None 
    option_type: Optional[Literal['CALL', 'PUT']] = None
    strike_price: Optional[float] = None
    underlying: Optional[str] = None

class MarketActivationRule(SerializableMixin):
    rule_type: Literal["Price"]
    symbol: str
    predicate: Literal["Lt", "Lte", "Gt", "Gte"]
    trigger_key: Literal["STT", "STTN", "SBA", "SAB", "DTT", "DTTN",
                        "DBA", "DAB", "TTT", "TTTN", "TBA", "TAB"]
    price: float
    logic_operator: Optional[Literal["And", "Or"]] = None

class TimeActivationRule(SerializableMixin):
    # Define fields based on actual structure if known
    time_utc: datetime

class Order(SerializableMixin):
    account_ID: str
    advanced_options: Optional[str] = None
    closed_date_time: Optional[datetime] = None
    commission_fee: Optional[str] = None
    conditional_orders: List[OrderRelationship] = Field(default_factory=list)
    conversion_rate: Optional[str] = None
    currency: Optional[str] = None
    duration: Optional[str] = None
    filled_price: Optional[str] = None
    good_till_date: Optional[datetime] = None
    group_name: Optional[str] = None
    legs: List[OrderLeg] = Field(default_factory=list)
    market_activation_rules: List[MarketActivationRule] = Field(default_factory=list)
    time_activation_rules: List[TimeActivationRule] = Field(default_factory=list)
    limit_price: Optional[str] = None
    opened_date_time: Optional[datetime] = None
    order_ID: Optional[str] = None
    order_type: OrderType
    price_used_for_buying_power: Optional[str] = None
    reject_reason: Optional[str] = None
    routing: Optional[str] = None
    show_only_quantity: Optional[str] = None
    spread: Optional[str] = None
    status: Optional[Literal["ACK", "ASS", "BRC", "BRF", "BRO", "CHG", "CND",
                             "COR", "DIS", "DOA", "DON", "ECN", "EXE", "FPR",
                             "LAT", "OPN", "OSO", "PLA", "REC", "RJC", "RPD",
                             "RSN", "STP", "STT", "SUS", "UCN", "CAN", "EXP",
                             "OUT", "RJR", "SCN", "TSC", "UCH", "REJ", "FLL",
                             "FLP", "OTHER"]] = None
    status_description: Optional[str] = None
    stop_price: Optional[str] = None
    trailing_stop: Optional[TrailingStop] = None
    unbundled_route_fee: Optional[str] = None
    
    @field_validator('advanced_options')
    @classmethod
    def validate_advanced_options(cls, value):
        if value is None:
            return value
        valid_static = {'CND', 'AON', 'TRL', 'NON', 'BKO', 'PSO'}
        valid_prefixes = ['SHWQTY=', 'DSCPR=', 'PEGVAL=']

        if value in valid_static:
            return value
        if any(value.startswith(prefix) for prefix in valid_prefixes):
            return value
        raise ValueError(f"Invalid advanced_options value: {value}")

class TimeInForceRequest(SerializableMixin):
    duration: Literal["DAY", "DYP", "GTC", "GCP", "GTD", "GDP", "OPG", "CLO", "IOC", "FOK", "1", "3", "5"]
    expiration: Optional[datetime] = None # For GTD, GDP orders

class TimeActivationRule(SerializableMixin):
    time_utc: datetime

class AdvancedOptions(SerializableMixin):
    add_liquidity: Optional[bool] = None
    all_or_none: Optional[bool] = None
    book_only: Optional[bool] = None
    discretionary_price: Optional[str] = None
    market_activation_rules: Optional[List[MarketActivationRule]] = None
    non_display: Optional[bool] = None
    peg_value: Optional[Literal["BEST", "MID"]] = None
    show_only_quantity: Optional[str] = None
    time_activation_rules: Optional[list[TimeActivationRule]] = None
    trailing_stop: Optional[TrailingStop] = None

class OrderRequestLeg(SerializableMixin):
    quantity: str
    symbol: str
    trade_action: TradeAction
    limit_price: Optional[str] = None

class OrderRequestOSO(SerializableMixin):
    type: Literal["NORMAL", "BRK", "OCO"]
    orders: List['OrderRequest']

class OrderRequest(SerializableMixin):
    account_ID: Optional[str] = None  # Optional here, may be omitted in OSO
    advanced_options: Optional[AdvancedOptions] = None
    buying_power_warning: Optional[Literal['Enforce', 'Preconfirmed', 'Confirmed']] = None
    legs: Optional[List[OrderRequestLeg]] = None
    order_confirm_ID: Optional[str] = None
    order_type: OrderType = "Market"
    quantity: str = "0"
    route: Optional[str] = None
    stop_price: Optional[str] = None
    symbol: str = ""
    time_in_force: TimeInForceRequest = Field(default_factory=TimeInForceRequest)
    trade_action: TradeAction = "BUY"
    OSOs: Optional[List[OrderRequestOSO]] = None  # Recursive nesting

OrderRequestOSO.model_rebuild()

class OrderError(SerializableMixin):
    account_ID: str
    error: str
    message: str

class Bar(SerializableMixin):
    open: float
    high: float
    low: float
    close: float
    down_ticks: int
    up_ticks: int
    total_ticks: int
    time_stamp: datetime
    down_volume: int
    up_volume: int
    total_volume: int
    epoch: int
    is_end_of_history: bool
    is_realtime: bool
    open_interest: int
    bar_status: Literal["Open", "Closed"]
    unchanged_volume: int # this is deprecated, will always be zero
    unchanged_ticks: int # this is deprecated, will always be zero
    
class Heartbeat(SerializableMixin):
    heartbeat: int
    timestamp: datetime

class Error(SerializableMixin):
    error: Literal['BadRequest', 'DualLogon', 'GoAway', 'InternalServerError']
    message: str
    
class ErrorResponse(SerializableMixin):
    error: Literal['BadRequest', 'Unauthorized', 'Forbidden', 'TooManyRequests', 'InternalServerError', 'NotImplemented', 'ServiceUnavailable', 'GatewayTimeout']
    message: str

class AccountDetail(SerializableMixin):
    day_trading_qualified: bool
    enrolled_in_reg_T_program: bool
    is_stock_locate_eligible: bool
    option_approval_level: int
    pattern_day_trader: bool
    requires_buying_power_warning: bool
 
class Account(SerializableMixin):
    account_ID: str
    account_type: Literal['Cash', 'Margin', 'Futures', 'DVP']
    currency: str
    status: Literal['Active', 'Closed', 'Closing Transaction Only', 'Margin Call - Closing Transactions Only',
                    'Inactive', 'Liquidating Transactions Only', 'Restricted', '90 Day Restriction-Closing Transaction Only']
    alias: Optional[str] = None
    alt_ID: Optional[str] = None
    account_detail: Optional[AccountDetail] = None
    
    
    
if __name__ == "__main__":
    # Example usage
    order = OrderRequest(
        account_ID="123456",
        order_type="Limit",
        quantity="100",
        symbol="AAPL",
        trade_action="BUY",
        legs=[
            OrderRequestLeg(
                quantity="100",
                symbol="AAPL",
                trade_action="BUY",
                limit_price="150.00"
            )
        ],
        advanced_options=AdvancedOptions(
            discretionary_price="149.50",
            trailing_stop=TrailingStop(amount="1.00")
        ),
        time_in_force=TimeInForceRequest(duration="GTC")
    )
    print(order.to_dict())
    print(OrderRequest.from_dict(order.to_dict()).to_dict())