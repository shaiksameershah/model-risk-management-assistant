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


def test_evidence_with_verbatim_prefix_is_accepted():
    source = "This is a rules-based hybrid model used in production."
    r = InventoryRecord()
    r.model_type = FieldValue(
        value="rules-based hybrid model",
        status="stated",
        evidence=["verbatim:rules-based hybrid model"],
    )
    apply_guards(r, source)
    assert r.model_type.status == "stated"


def test_evidence_with_quoted_prefix_and_quotes_is_accepted():
    source = "Inputs are retail and commercial transaction records."
    r = InventoryRecord()
    r.input_data = FieldValue(
        value="retail and commercial transaction records",
        status="stated",
        evidence=["Quoted 'retail and commercial transaction records'"],
    )
    apply_guards(r, source)
    assert r.input_data.status == "stated"


def test_evidence_wrapped_in_double_quotes_is_accepted():
    source = "The AML Transaction Monitoring Model is used by analysts."
    r = InventoryRecord()
    r.model_name = FieldValue(
        value="AML Transaction Monitoring Model",
        status="stated",
        evidence=['"AML Transaction Monitoring Model"'],
    )
    apply_guards(r, source)
    assert r.model_name.status == "stated"
