from inspect import isclass

from typing import Any, Dict, List, Tuple


# TODO improve handling of non-string keys


def _find_type_errors(value, _type):
    if not isinstance(type(_type), type):
        raise ValueError("_type must be a type, but got: {}".format(_type))
    if not isclass(_type):  # Any and Union are types but aren't classes
        if _type is Any:
            yield from ()
        else:
            for branch in _type.__args__:
                errors = list(_find_type_errors(value, branch))
                if not errors:
                    break
            else:  # no break means no matching branch
                yield "{!r} is not in {}".format(value, _type)
    else:
        if isinstance(_type, JsonRecord):
            if not isinstance(value, _type):
                yield "{!r} is not of type {}".format(value, _type)
            else:
                for f, f_type in _type.schema.items():
                    yield from ("""["{}"]: {}""".format(f, e) for e in _find_type_errors(value.get(f), f_type))
        elif issubclass(_type, Dict):
            if not isinstance(value, Dict):
                yield "{!r} is not of type {}".format(value, _type)
            else:
                k_type, v_type = _type.__args__
                for k, v in value.items():
                    yield from ("invalid key: {}".format(e) for e in _find_type_errors(k, k_type))
                    yield from ("invalid value: {}".format(e) for e in _find_type_errors(v, v_type))
        elif issubclass(_type, List):
            if not isinstance(value, List):
                yield "{!r} is not of type {}".format(value, _type)
            else:
                i_type, = _type.__args__  # args is a 1-tuple so we need the trailing comma
                for i in value:
                    yield from ("invalid element: {}".format(e) for e in _find_type_errors(i, i_type))
        elif issubclass(_type, Tuple):
            if not isinstance(value, (Tuple, List)):
                yield "{!r} is not of type {}".format(value, _type)
            else:
                for index, (i, i_type) in enumerate(zip(value, _type.__args__)):
                    yield from ("invalid element at index {}: {}".format(index, e) for e in _find_type_errors(i, i_type))
        else:
            if _type is int and type(value) is bool:
                yield "{!r} is not of type {}".format(value, _type)
            else:
                if _type is float:
                    _type = (int, float)
                if not isinstance(value, _type):
                    yield "{!r} is not of type {}".format(value, _type)


def _assert_isinstance(value, _type):
    """Check if a value conforms to a type (recursively for collections and records)."""
    print("{}:{}".format(value, _type))
    errors = list(_find_type_errors(value, _type))
    if errors:
        raise TypeError("; ".join(errors))
    else:
        return


def _coerce_records(value, _type):
    """Coerce dictionaries into record types where appropriate."""
    if not isinstance(type(_type), type):
        raise ValueError("_type must be a type, but got: {}".format(_type))
    if not isclass(_type):  # Any and Union are types but aren't classes
        if _type is Any:
            return value
        for branch in _type.__args__:  # return the first coercion that sticks
            if isinstance(branch, JsonRecord):
                try:
                    return branch(value)
                except TypeError:
                    pass
            elif issubclass(branch, Dict):
                try:
                    _assert_isinstance(value, branch)
                    return value
                except TypeError:
                    pass
        return value
    else:
        if isinstance(_type, JsonRecord):
            return _type(value)
        elif issubclass(_type, List):
            if isinstance(value, List):
                e_type, = _type.__args__
                return [_coerce_records(e, e_type) for e in value]
            return value
        elif issubclass(_type, Tuple):
            if isinstance(value, (Tuple, List)):
                return [_coerce_records(e, index_type) for e, index_type in zip(value, _type.__args__)]
            return value
        elif issubclass(_type, Dict):
            if isinstance(value, Dict):
                k_type, v_type = _type.__args__
                return {k: _coerce_records(v, v_type) for k, v in value.items()}
            return value
        else:
            return value


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
    def __new__(mcs, name, bases, dct):
        class _JsonRecordSuper(dict):
            def __init__(self, *a, **kw):
                for a_dict in a + (kw,):
                    for k, v in a_dict.items():
                        self[k] = v
                _assert_isinstance(self, type(self))

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
                _type = type(self).schema[key]
                value = _coerce_records(value, _type)
                _assert_isinstance(value, _type)
                super(_JsonRecordSuper, self).__setitem__(key, value)

            def __setattr__(self, key, value):
                self[key] = value

            def __repr__(self):
                return "{}({})".format(name, dict(self))

        return super(JsonRecord, mcs).__new__(mcs, name, bases + (_JsonRecordSuper,), dct)
