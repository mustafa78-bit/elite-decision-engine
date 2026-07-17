from dataclasses import dataclass
from core.serialization import SerializableMixin, serialize_list


@dataclass
class _SerTestModel(SerializableMixin):
    name: str = ""
    value: int = 0


@dataclass
class _SerItem(SerializableMixin):
    id: int = 0


class TestSerializableMixin:

    def test_to_dict_basic(self):
        obj = _SerTestModel(name="test", value=42)
        d = obj.to_dict()
        assert d["name"] == "test"
        assert d["value"] == 42

    def test_from_dict(self):
        obj = _SerTestModel.from_dict({"name": "test", "value": 42})
        assert obj.name == "test"
        assert obj.value == 42


class TestSerializeList:

    def test_serialize_list(self):
        items = [_SerItem(1), _SerItem(2)]
        result = serialize_list(items)
        assert result == [{"id": 1}, {"id": 2}]

    def test_serialize_list_dicts(self):
        result = serialize_list([{"a": 1}, {"b": 2}])
        assert result == [{"a": 1}, {"b": 2}]
