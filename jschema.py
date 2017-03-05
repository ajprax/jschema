import json
from inspect import isclass

from typing import Dict, List, Tuple


# TODO improve handling of non-string keys


def assert_type(value, _type):
    """Check if a value conforms to a type (recursively for collections and records)."""
    assert isinstance(type(_type), type), "_type must be a type, but got: {}".format(_type)
    if not isclass(_type):  # Union is a type but isn't a class, so issubclass would raise
        try:
            for union_branch in _type.__args__:
                try:
                    assert_type(value, union_branch)
                    break
                except AssertionError:
                    pass
            else:  # no break means no match
                assert False, "{} is not in {}".format(value, _type)
        except AttributeError:
            assert False, "Unrecognized non-class type {}".format(_type)
    else:
        if isinstance(_type, JsonRecord):
            assert isinstance(value, _type), "{} is not of type {}".format(value, type.__name__)
            for f, f_type in _type.schema.items():
                assert_type(value.get(f), f_type)
        elif issubclass(_type, Dict):
            k_type, v_type = _type.__args__
            for k, v in value.items():
                assert_type(k, k_type)  # kind of meaningless since keys have to be str
                assert_type(v, v_type)
        elif issubclass(_type, List):
            e_type, = _type.__args__  # args is a 1-tuple for list, so the trailing comma is needed
            for e in value:
                assert_type(e, e_type)
        elif issubclass(_type, Tuple):
            for item, union_branch in zip(value, _type.__args__):
                assert_type(item, union_branch)
            return
        else:
            assert isinstance(value, _type), "{} is not of type {}".format(value, _type.__name__)


class JsonRecord(type):
    """
    Metaclass for records which can be represented in JSON.

    Enforces types according to the schema provided. Schema is defined as a dictionary of field
    names mapped to types (primitive types, List, Dict, Tuple, Optional, other record types).

    class ExampleRecord(metaclass=JsonRecord):
        schema = {
            "field": str,
            "optional_field": Optional[int],
            "complex_field": Dict[str, List[Union[int, bool, str]]],
        }
    """
    def __new__(meta, name, bases, dct):
        class _JsonRecordSuper(dict):
            @classmethod
            def from_dict(cls, _dct):
                fs = {}
                for field, _type in cls.schema.items():
                    if isinstance(_type, JsonRecord):
                        fs[field] = _type.from_dict(_dct.get(field, {}))
                    elif field in _dct:
                        fs[field] = _dct[field]
                return cls(**fs)

            @classmethod
            def from_json(cls, json_str):
                return cls.from_dict(json.loads(json_str))

            def to_json(self):
                return json.dumps(self)

            def __init__(self, **kw):
                for field, typ in dct["schema"].items():
                    value = kw.get(field)
                    assert_type(value, typ)
                    # we want to check the type even if the value is absent since the type must be
                    # Optional, but we only want to set present values
                    if field in kw:
                        self[field] = value

            def __getattr__(self, item):
                return self.get(item)  # get instead of getitem so absent Optionals return None

            def __setattr__(self, key, value):
                assert_type(value, type(self).schema[key])
                self[key] = value

            def __repr__(self):
                return "{}({})".format(name, dict(self))

        return super(JsonRecord, meta).__new__(meta, name, bases + (_JsonRecordSuper,), dct)
