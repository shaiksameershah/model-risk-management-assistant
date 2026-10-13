from pathlib import Path

MODEL_NAME = "deepseek-r1:7b"
OLLAMA_HOST = "http://localhost:11434"
TEMPERATURE = 0.0
SEED = 42
NUM_CTX = 8192

OUTPUT_DIR = Path("data/out")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FIELD_GROUPS = {
    "identity": ["model_name", "model_id", "business_function", "business_owner"],
    "ownership": ["model_owner", "development_team"],
    "purpose": ["business_purpose", "intended_use", "downstream_uses", "output_variables"],
    "methodology": ["model_type", "methodology"],
    "assumptions": ["key_assumptions", "limitations"],
    "data": ["input_data", "data_sources"],
    "lifecycle": [
        "model_status", "lifecycle_stage", "validation_status",
        "last_validation_date", "monitoring_approach",
    ],
    "risk": [
        "known_weaknesses", "remediation_actions",
        "third_party_dependencies", "proposed_risk_considerations",
    ],
    "environment": ["development_approach", "implementation_environment"],
}

FRAMEWORK_MAPPING: dict[str, str] = {}
