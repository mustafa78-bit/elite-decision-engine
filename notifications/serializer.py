import json
from datetime import UTC, datetime, timezone


def serialize_event(event: str, payload: dict) -> str:
    return json.dumps({
        "event": event,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    })
