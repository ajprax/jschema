# jschema
Schema enforcement for JSON records

```python
class MyRecord(metaclass=JsonRecord):
    schema = {
        "foo": str,
        "bar": int,
        "baz": Optional[Dict[str, List[Tuple[str, Union[bool, str, AnotherRecord]]]]],
    }

my_record = MyRecord(foo="foo", bar=5, baz={"k": [["v", AnotherRecord()], ["v2", True]]})
print(my_record["foo"])
my_record.bar = 10
my_other_record = MyRecord(json.loads(json.dumps(my_record)))
```

JsonRecords subclass dict and support dict and accessor style access. Records do not support setting
fields not found in the schema. Values types are checked on record instantiation, when being set,
and during serialization.

Field types may be basic JSON serializable types (str, int, float, bool, List, Dict) as well as
Optional (matches None/null or absent values), Tuple (heterogeneous list typed by index), and Union.
