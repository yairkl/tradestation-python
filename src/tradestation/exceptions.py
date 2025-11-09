"""Custom exceptions for TradeStation API."""


class TradeStationError(Exception):
    """Base exception for TradeStation API errors."""
    pass


class AuthenticationError(TradeStationError):
    """Raised when authentication fails."""
    pass


class APIError(TradeStationError):
    """Raised when API returns an error response."""
    
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    pass


class OrderError(APIError):
    """Raised when order operations fail."""
    pass


class StreamError(TradeStationError):
    """Raised when streaming operations fail."""
    pass
