from inspect import isclass

from typing import Any, Dict, List, Tuple


# TODO improve handling of non-string keys


def _assert_isinstance(value, _type):
    """Check if a value conforms to a type (recursively for collections and records)."""
    if not isinstance(type(_type), type):
        raise ValueError("_type must be a type, but got: {}".format(_type))
    if not isclass(_type):  # Any and Union are types but aren't classes
        if _type is Any:
            return
        try:
            for union_branch in _type.__args__:
                try:

                    _assert_isinstance(value, union_branch)
                    break
                except TypeError:
                    pass
            else:  # no break means no match
                raise TypeError("{!r} is not in {}".format(value, _type))
        except AttributeError:
            raise ValueError("Unrecognized non-class type {}".format(_type))
    else:
        if isinstance(_type, JsonRecord):
            if not isinstance(value, _type):
                raise TypeError("{!r} is not of type {}".format(value, _type))
            for f, f_type in _type.schema.items():
                _assert_isinstance(value.get(f), f_type)
        elif issubclass(_type, Dict):
            if not isinstance(value, Dict):
                raise TypeError("{!r} is not of type {}".format(value, _type))
            k_type, v_type = _type.__args__
            for k, v in value.items():
                _assert_isinstance(k, k_type)  # kind of meaningless since keys have to be str
                _assert_isinstance(v, v_type)
        elif issubclass(_type, List):
            if not isinstance(value, List):
                raise TypeError("{!r} is not of type {}".format(value, _type))
            e_type, = _type.__args__  # args is a 1-tuple for list, so the trailing comma is needed
            for e in value:
                _assert_isinstance(e, e_type)
        elif issubclass(_type, Tuple):
            if not isinstance(value, (Tuple, List)):
                raise TypeError("{!r} is not of type {}".format(value, _type))
            for item, union_branch in zip(value, _type.__args__):
                _assert_isinstance(item, union_branch)
        else:
            if _type is int and type(value) is bool:  # bool passes isinstance(b, int)
                raise TypeError("{!r} is not of type {}".format(value, _type))
            if _type is float:  # JSON numbers may be parsed as ints when we expect floats
                _type = (int, float)
            if not isinstance(value, _type):
                raise TypeError("{!r} is not of type {}".format(value, _type))


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
            def __init__(self, *a, **kw):
                for a_dict in a + (kw,):
                    for k, v in a_dict.items():
                        self[k] = v
                for f, f_type in type(self).schema.items():
                    # TODO find a way to only check for presence of required fields
                    _assert_isinstance(self[f], f_type)

            def _validate_key(self, key):
                if key not in type(self).schema:
                    raise KeyError(key)

            def __getitem__(self, item):
                self._validate_key(item)
                return self.get(item)  # absent Optionals should return None

            def __getattr__(self, item):
                return self[item]

            def __setitem__(self, key, value):
                self._validate_key(key)
                _assert_isinstance(value, type(self).schema[key])
                super(_JsonRecordSuper, self).__setitem__(key, value)

            def __setattr__(self, key, value):
                self[key] = value

            def __repr__(self):
                return "{}({})".format(name, dict(self))

        return super(JsonRecord, meta).__new__(meta, name, bases + (_JsonRecordSuper,), dct)
