from typing import Optional, List, Union, Tuple, Dict

from . import JsonRecord


class StrRecord(metaclass=JsonRecord):
    schema = {"str": str}


class BoolRecord(metaclass=JsonRecord):
    schema = {"bool": bool}


class IntRecord(metaclass=JsonRecord):
    schema = {"int": int}


class FloatRecord(metaclass=JsonRecord):
    schema = {"float": float}


class OptionalRecord(metaclass=JsonRecord):
    schema = {"opt": Optional[str]}


class ListRecord(metaclass=JsonRecord):
    schema = {"list": List[str]}


class DictRecord(metaclass=JsonRecord):
    schema = {"dict": Dict[str, int]}


class TupleRecord(metaclass=JsonRecord):
    schema = {"tuple": Tuple[str, int]}


class UnionRecord(metaclass=JsonRecord):
    schema = {"union": Union[str, int]}


class NestedRecord(metaclass=JsonRecord):
    class InnerRecord(metaclass=JsonRecord):
        schema = {"foo": str}

    schema = {
        "inner": InnerRecord
    }


def test_constructor():
    assert StrRecord(str="bar").str == "bar"
    assert StrRecord({"str": "bar"}).str == "bar"
    assert StrRecord({"str": "bar"}, str="baz").str == "baz"
    assert StrRecord({"str": "bar"}, {"str": "baz"}).str == "baz"
    assert StrRecord({"str": "bar"}, {"str": "baz"}, str="qux").str == "qux"
    try:
        StrRecord()
        assert False
    except TypeError:
        pass
    try:
        StrRecord(bar="baz")
        assert False
    except KeyError:
        pass


def test_str():
    assert StrRecord(str="str").str == "str"
    try:
        StrRecord()
        assert False
    except TypeError:
        pass
    try:
        StrRecord(str=5)
        assert False
    except TypeError:
        pass


def test_bool():
    assert BoolRecord(bool=True).bool is True
    try:
        BoolRecord()
        assert False
    except TypeError:
        pass
    try:
        BoolRecord(bool=5)
        assert False
    except TypeError:
        pass


def test_int():
    assert IntRecord(int=5).int == 5
    try:
        IntRecord()
        assert False
    except TypeError:
        pass
    try:
        IntRecord(int="5")
        assert False
    except TypeError:
        pass


def test_float():
    assert FloatRecord(float=0.5).float == 0.5
    assert FloatRecord(float=5).float == 5
    try:
        FloatRecord()
        assert False
    except TypeError:
        pass
    try:
        FloatRecord(float="0.5")
        assert False
    except TypeError:
        pass


def test_optional():
    assert OptionalRecord(opt="opt").opt == "opt"
    assert OptionalRecord().opt is None
    try:
        OptionalRecord(opt=5)
        assert False
    except TypeError:
        pass

def test_list():
    assert ListRecord(list=[]).list == []
    assert ListRecord(list=["e"]).list == ["e"]
    try:
        ListRecord()
        assert False
    except TypeError:
        pass
    try:
        ListRecord(list="abc")
        assert False
    except TypeError:
        pass

def test_dict():
    assert DictRecord(dict={}).dict == {}
    assert DictRecord(dict={"a": 1}).dict == {"a": 1}
    try:
        DictRecord()
        assert False
    except TypeError:
        pass
    try:
        DictRecord(dict=[("a", 1)])
        assert False
    except TypeError:
        pass

def test_tuple():
    assert TupleRecord(tuple=("a", 1)).tuple == ["a", 1]
    assert TupleRecord(tuple=["a", 1]).tuple == ["a", 1]
    try:
        TupleRecord()
        assert False
    except TypeError:
        pass
    try:
        TupleRecord(tuple={"a": 1})
        assert False
    except TypeError:
        pass

def test_union():
    assert UnionRecord(union="union").union == "union"
    assert UnionRecord(union=5).union == 5
    try:
        UnionRecord()
        assert False
    except TypeError:
        pass
    try:
        UnionRecord(union=[])
        assert False
    except TypeError:
        pass

def test_nested():
    inner = NestedRecord.InnerRecord(foo="bar")
    assert NestedRecord(inner=inner).inner == inner
    try:
        NestedRecord()
        assert False
    except TypeError:
        pass
    try:
        NestedRecord(inner=5)
        assert False
    except TypeError:
        pass
