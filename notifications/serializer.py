import json
from datetime import datetime, timezone


def serialize_event(event: str, payload: dict) -> str:
    return json.dumps({
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    })
