from dataclasses import asdict
from typing import Any, Dict, List


class SerializableMixin:

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SerializableMixin":
        return cls(**data)


def serialize_list(items: List[Any]) -> List[Dict[str, Any]]:
    return [item.to_dict() if hasattr(item, "to_dict") else item for item in items]
