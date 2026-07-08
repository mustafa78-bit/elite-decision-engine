class ExchangeError(Exception):
    """Base exchange error."""

class ConnectionError(ExchangeError):
    """Failed to connect to exchange."""

class AuthenticationError(ExchangeError):
    """Invalid or missing API credentials."""

class RateLimitError(ExchangeError):
    """Rate limit exceeded."""

class OrderError(ExchangeError):
    """Order-related error."""

class InsufficientFunds(OrderError):
    """Not enough balance to place order."""

class InvalidOrder(OrderError):
    """Invalid order parameters."""

class OrderNotFound(OrderError):
    """Order not found."""

class PositionNotFound(ExchangeError):
    """Position not found."""

class SymbolNotFound(ExchangeError):
    """Symbol not found on exchange."""

class MarketDataError(ExchangeError):
    """Failed to fetch market data."""

class TimeoutError(ExchangeError):
    """Request timed out."""
