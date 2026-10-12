from mrm.schema import InventoryRecord, FieldValue
from mrm.validate import apply_guards


def test_ungrounded_evidence_is_downgraded():
    r = InventoryRecord()
    r.model_owner = FieldValue(
        value="Someone Not In Source", status="stated",
        evidence=["this quote does not exist anywhere"],
    )
    apply_guards(r, "the source text mentions nobody by name")
    assert r.model_owner.status == "unknown"


def test_grounded_evidence_survives():
    source = "The model owner is Priya Raman."
    r = InventoryRecord()
    r.model_owner = FieldValue(
        value="Priya Raman", status="stated",
        evidence=["The model owner is Priya Raman"],
    )
    apply_guards(r, source)
    assert r.model_owner.status == "stated"


def test_date_not_in_source_is_downgraded():
    r = InventoryRecord()
    r.last_validation_date = FieldValue(
        value="2023-01-01", status="stated",
        evidence=["validated on 2023-01-01"],
    )
    apply_guards(r, "the model was never validated")
    assert r.last_validation_date.status == "unknown"
