from mrm.schema import InventoryRecord, FieldValue


def test_default_record_has_all_fields_unknown():
    r = InventoryRecord()
    assert r.model_name.status == "unknown"
    assert r.last_validation_date.value is None


def test_field_value_serialises():
    fv = FieldValue(value="x", status="stated", evidence=["x"], confidence=1.0)
    assert fv.model_dump()["status"] == "stated"


def test_list_value_is_coerced_to_string():
    fv = FieldValue(value=["one", "two"], status="stated", evidence=[])
    assert fv.value == "one two"
