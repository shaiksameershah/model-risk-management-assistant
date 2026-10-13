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


def test_model_type_identical_to_model_name_is_nulled():
    source = "The Customer Churn Propensity Model estimates churn."
    r = InventoryRecord()
    r.model_name = FieldValue(
        value="Customer Churn Propensity Model",
        status="stated",
        evidence=["The Customer Churn Propensity Model"],
    )
    r.model_type = FieldValue(
        value="Customer Churn Propensity Model",
        status="stated",
        evidence=["The Customer Churn Propensity Model"],
    )
    apply_guards(r, source)
    assert r.model_type.status == "unknown"
    assert any("identical_to_model_name" in e for e in r.model_type.evidence)


def test_distinct_model_type_survives():
    source = ("The Retail Credit Scorecard is a logistic regression model "
              "used for PD estimation.")
    r = InventoryRecord()
    r.model_name = FieldValue(
        value="Retail Credit Scorecard",
        status="stated",
        evidence=["The Retail Credit Scorecard"],
    )
    r.model_type = FieldValue(
        value="logistic regression",
        status="stated",
        evidence=["a logistic regression model"],
    )
    apply_guards(r, source)
    assert r.model_type.status == "stated"


def test_input_data_from_assess_verb_is_rejected():
    source = "The Climate Transition Risk Model assesses the bank's corporate lending portfolio."
    r = InventoryRecord()
    r.input_data = FieldValue(
        value="bank's corporate lending portfolio",
        status="stated",
        evidence=["assesses the bank's corporate lending portfolio"],
    )
    apply_guards(r, source)
    assert r.input_data.status == "unknown"
    assert any("verb_of_analysis" in e for e in r.input_data.evidence)


def test_input_data_from_explicit_input_language_survives():
    source = "Inputs are position data from the trading systems and 500 days of historical market data."
    r = InventoryRecord()
    r.input_data = FieldValue(
        value="position data from the trading systems",
        status="stated",
        evidence=["Inputs are position data from the trading systems"],
    )
    apply_guards(r, source)
    assert r.input_data.status == "stated"
