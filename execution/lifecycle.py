"""Paper trading state machine and lifecycle validation.

Defines valid transitions and guards for PaperOrder and PaperTrade/PaperPosition
lifecycles. All validation functions raise ``ValueError`` on invalid transitions.
"""

from __future__ import annotations

from database import (
    CANCEL,
    CLOSED,
    FILLED,
    OPEN,
    PARTIALLY_FILLED,
    PENDING,
    STOP_LOSS,
    TAKE_PROFIT,
    ORDER_FINAL_STATUSES,
    TRADE_FINAL_STATUSES,
)

# ---------------------------------------------------------------------------
# State transition maps
# ---------------------------------------------------------------------------

ORDER_TRANSITIONS: dict[str, set[str]] = {
    PENDING: {FILLED, PARTIALLY_FILLED, CANCEL},
    PARTIALLY_FILLED: {FILLED, CANCEL},
    FILLED: set(),
    CANCEL: set(),
}

TRADE_TRANSITIONS: dict[str, set[str]] = {
    OPEN: {TAKE_PROFIT, STOP_LOSS, CLOSED, CANCEL},
    TAKE_PROFIT: set(),
    STOP_LOSS: set(),
    CLOSED: set(),
    CANCEL: set(),
}

_ALL_ORDER_STATUSES = frozenset(ORDER_TRANSITIONS.keys())
_ALL_TRADE_STATUSES = frozenset(TRADE_TRANSITIONS.keys())


# ---------------------------------------------------------------------------
# Transition validation
# ---------------------------------------------------------------------------


def validate_order_transition(current: str, new: str) -> None:
    """Raise ``ValueError`` if the order state transition is invalid."""
    _validate_known_status(current, _ALL_ORDER_STATUSES, "order")
    _validate_known_status(new, _ALL_ORDER_STATUSES, "order")

    allowed = ORDER_TRANSITIONS.get(current, set())
    if new not in allowed:
        path = f"{current} -> {new}"
        if current in ORDER_FINAL_STATUSES:
            msg = f"Order is in terminal status {current}: cannot transition to {new}"
        else:
            msg = f"Invalid order transition: {path}"
        raise ValueError(msg)


def validate_trade_transition(current: str, new: str) -> None:
    """Raise ``ValueError`` if the trade/position state transition is invalid."""
    _validate_known_status(current, _ALL_TRADE_STATUSES, "trade")
    _validate_known_status(new, _ALL_TRADE_STATUSES, "trade")

    allowed = TRADE_TRANSITIONS.get(current, set())
    if new not in allowed:
        path = f"{current} -> {new}"
        if current in TRADE_FINAL_STATUSES:
            msg = f"Trade is in terminal status {current}: cannot transition to {new}"
        else:
            msg = f"Invalid trade transition: {path}"
        raise ValueError(msg)


def is_valid_order_transition(current: str, new: str) -> bool:
    try:
        validate_order_transition(current, new)
        return True
    except ValueError:
        return False


def is_valid_trade_transition(current: str, new: str) -> bool:
    try:
        validate_trade_transition(current, new)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Terminal status checks
# ---------------------------------------------------------------------------


def is_order_terminal(status: str) -> bool:
    return status in ORDER_FINAL_STATUSES


def is_trade_terminal(status: str) -> bool:
    return status in TRADE_FINAL_STATUSES


# ---------------------------------------------------------------------------
# Idempotent helpers
# ---------------------------------------------------------------------------


def validate_fill_order(current: str) -> None:
    """Validate that an order can be filled."""
    if current == CANCEL:
        raise ValueError("A cancelled order cannot be filled")
    if current == FILLED:
        raise ValueError("An already filled order cannot be filled again")
    validate_order_transition(current, FILLED)


def validate_cancel_order(current: str) -> bool:
    """Return True if cancel is allowed, False if already cancelled (idempotent).

    Raises ``ValueError`` if the order is in a terminal non-cancelled state
    (e.g. FILLED) where cancel is forbidden.
    """
    if current == CANCEL:
        return False
    if current == FILLED:
        raise ValueError("A filled order cannot be cancelled")
    validate_order_transition(current, CANCEL)
    return True


def validate_close_trade(current: str, new: str = CLOSED) -> bool:
    """Return True if close is allowed, False if already terminal (idempotent).

    Raises ``ValueError`` if the transition is invalid from the current state.
    """
    if current in TRADE_FINAL_STATUSES:
        return False
    validate_trade_transition(current, new)
    return True


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_known_status(status: str, known: frozenset, kind: str) -> None:
    if status not in known:
        raise ValueError(f"Unknown {kind} status: {status!r}")
