"""
TradeStation API Python Client

A comprehensive Python library for interacting with the TradeStation API.
Supports market data, trading, account management, and streaming.
"""

__version__ = "0.1.0"
__author__ = "Yair Klein"
__license__ = "MIT"

from .client import TradeStationClient
from .exceptions import (
    TradeStationError,
    AuthenticationError,
    APIError,
    RateLimitError,
    OrderError,
)

__all__ = [
    "TradeStationClient",
    "TradeStationError",
    "AuthenticationError",
    "APIError",
    "RateLimitError",
    "OrderError",
]