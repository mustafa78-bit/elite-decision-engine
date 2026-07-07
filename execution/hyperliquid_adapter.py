"""Read-only Hyperliquid API adapter.

Supports only GET-like queries via POST to the Hyperliquid /info endpoint.
NEVER creates, cancels, or modifies orders.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import requests

INFO_URL = "https://api.hyperliquid.xyz/info"


@dataclass(frozen=True)
class AccountState:
    address: str
    account_value: float = 0.0
    withdrawable: float = 0.0
    total_margin: float = 0.0
    positions: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class OpenOrder:
    coin: str = ""
    side: str = ""
    limit_px: float = 0.0
    sz: float = 0.0
    order_type: str = ""
    order_id: int = 0
    status: str = ""
    timestamp: int = 0
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Position:
    coin: str = ""
    size: float = 0.0
    entry_px: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    leverage: dict = field(default_factory=dict)
    liquidation_px: float = 0.0
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Balance:
    coin: str = ""
    total: float = 0.0
    withdrawable: float = 0.0
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ExchangeStatus:
    status: str = ""
    contracts_open: int = 0
    raw: dict = field(default_factory=dict)


class HyperliquidReadOnlyAdapter:
    """Read-only adapter for the Hyperliquid API.

    All methods POST to ``/info`` and parse the JSON response.
    The ``session`` parameter is injectable for testing.
    """

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(__name__)

    def get_account_state(self, address: str) -> AccountState:
        """Fetch full account state including positions and margin."""
        self.logger.info("Fetching account state for %s", address)
        data = self._post({"type": "clearinghouseState", "user": address})

        asset_positions = data.get("assetPositions", [])
        positions = [self._parse_position(p) for p in asset_positions]

        account_value = self._safe_float(data.get("accountValue"))
        withdrawable = self._safe_float(data.get("withdrawable"))
        total_margin = sum(
            self._safe_float(p.get("position", {}).get("margin"))
            for p in asset_positions
            if isinstance(p, dict)
        )

        self.logger.info(
            "Account %s: value=%s withdrawable=%s positions=%s",
            address, account_value, withdrawable, len(positions),
        )
        return AccountState(
            address=address,
            account_value=account_value,
            withdrawable=withdrawable,
            total_margin=total_margin,
            positions=positions,
            raw=data,
        )

    def get_open_orders(self, address: str) -> list[OpenOrder]:
        """Fetch all open orders for the given address."""
        self.logger.info("Fetching open orders for %s", address)
        data = self._post({"type": "openOrders", "user": address})
        orders = [self._parse_order(o) for o in data if isinstance(o, dict)]
        self.logger.info("Open orders for %s: %s", address, len(orders))
        return orders

    def get_positions(self, address: str) -> list[Position]:
        """Fetch all open positions from account state."""
        state = self.get_account_state(address)
        self.logger.info(
            "Open positions for %s: %s",
            address, len(state.positions),
        )
        return state.positions

    def get_balance(self, address: str) -> list[Balance]:
        """Fetch balance information from account state."""
        self.logger.info("Fetching balance for %s", address)
        data = self._post({"type": "clearinghouseState", "user": address})

        withdrawable = self._safe_float(data.get("withdrawable"))
        account_value = self._safe_float(data.get("accountValue"))

        balances = [
            Balance(
                coin="USD",
                total=account_value,
                withdrawable=withdrawable,
                raw=data,
            ),
        ]

        spot_assets = data.get("spotAssets", [])
        for asset in spot_assets:
            if isinstance(asset, dict):
                coin = asset.get("coin", "")
                total = self._safe_float(asset.get("total"))
                wd = self._safe_float(asset.get("withdrawable"))
                balances.append(
                    Balance(coin=coin, total=total, withdrawable=wd, raw=asset),
                )

        self.logger.info("Balance for %s: %s entries", address, len(balances))
        return balances

    def get_exchange_status(self) -> ExchangeStatus:
        """Fetch exchange status."""
        self.logger.info("Fetching exchange status")
        data = self._post({"type": "exchangeStatus"})
        status = str(data.get("status", ""))
        contracts_open = int(data.get("contractsOpen", 0))
        self.logger.info("Exchange status: %s", status)
        return ExchangeStatus(
            status=status,
            contracts_open=contracts_open,
            raw=data,
        )

    def get_metadata(self) -> dict:
        """Fetch exchange metadata (universe, specs)."""
        self.logger.info("Fetching exchange metadata")
        data = self._post({"type": "meta"})
        universe = data.get("universe", [])
        self.logger.info("Exchange metadata: %s assets", len(universe))
        return dict(data)

    def get_order_status(self, address: str, order_id: int) -> dict:
        """Fetch status of a specific order (read-only)."""
        self.logger.info("Fetching order status for %s order %s", address, order_id)
        data = self._post({
            "type": "orderStatus",
            "user": address,
            "oid": order_id,
        })
        self.logger.info("Order %s status: %s", order_id, data.get("status", "?"))
        return dict(data)

    def _post(self, payload: dict) -> Any:
        """Send a POST request to the Hyperliquid /info endpoint."""
        self.logger.debug("POST %s payload=%s", INFO_URL, payload)
        response = self.session.post(INFO_URL, json=payload, timeout=20)
        response.raise_for_status()
        return response.json()

    def _parse_position(self, raw: Any) -> Position:
        if not isinstance(raw, dict):
            return Position(raw={})
        pos = raw.get("position", raw) if "position" in raw else raw
        return Position(
            coin=str(pos.get("coin", "")),
            size=self._safe_float(pos.get("szi") or pos.get("size", 0)),
            entry_px=self._safe_float(pos.get("entryPx") or pos.get("entry", 0)),
            unrealized_pnl=self._safe_float(
                pos.get("unrealizedPnl") or pos.get("unrealized_pnl", 0),
            ),
            realized_pnl=self._safe_float(
                pos.get("realizedPnl") or pos.get("realized_pnl", 0),
            ),
            leverage=pos.get("leverage", {}),
            liquidation_px=self._safe_float(
                pos.get("liquidationPx") or pos.get("liquidation_px", 0),
            ),
            raw=raw,
        )

    def _parse_order(self, raw: dict) -> OpenOrder:
        return OpenOrder(
            coin=str(raw.get("coin", "")),
            side=str(raw.get("side", "")),
            limit_px=self._safe_float(raw.get("limitPx", 0)),
            sz=self._safe_float(raw.get("sz", 0)),
            order_type=str(raw.get("orderType", "")),
            order_id=int(raw.get("oid", 0)),
            status=str(raw.get("status", "")),
            timestamp=int(raw.get("timestamp", 0)),
            raw=raw,
        )

    @staticmethod
    def _safe_float(value: Any) -> float:
        if value is None:
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
