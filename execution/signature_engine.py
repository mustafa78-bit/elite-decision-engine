from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SignedPayload:
    order: Any
    signature: str
    signing_timestamp: str
    signer: str = "simulated-v1"


class SignatureEngine:

    def __init__(self, signer: str = "simulated-v1") -> None:
        self.signer = signer

    def sign(self, payload: Any) -> SignedPayload:
        signing_ts = datetime.now(timezone.utc).isoformat()

        return SignedPayload(
            order=payload,
            signature=self._compute_signature(payload, signing_ts),
            signing_timestamp=signing_ts,
            signer=self.signer,
        )

    def _compute_signature(self, payload: Any, timestamp: str) -> str:
        parts = [
            str(getattr(payload, "symbol", "")),
            str(getattr(payload, "side", "")),
            str(getattr(payload, "price", "")),
            str(getattr(payload, "quantity", "")),
            str(getattr(payload, "client_order_id", "")),
            timestamp,
        ]
        raw = ":".join(parts)
        logger.debug("Signing raw: %s", raw)
        return f"SIMULATED_SIG:{hash(raw)}"
