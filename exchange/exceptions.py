class ExchangeError(Exception):
    """Base exchange error."""

class ExchangeConnectionError(ExchangeError):
    """Failed to connect to exchange."""

class AuthenticationError(ExchangeError):
    """Invalid or missing API credentials."""

class RateLimitError(ExchangeError):
    """Rate limit exceeded."""

class OrderError(ExchangeError):
    """Order-related error."""

class InsufficientFundsError(OrderError):
    """Not enough balance to place order."""

class InvalidOrderError(OrderError):
    """Invalid order parameters."""

class OrderNotFoundError(OrderError):
    """Order not found."""

class PositionNotFoundError(ExchangeError):
    """Position not found."""

class SymbolNotFoundError(ExchangeError):
    """Symbol not found on exchange."""

class MarketDataError(ExchangeError):
    """Failed to fetch market data."""

class ExchangeTimeoutError(ExchangeError):
    """Request timed out."""
