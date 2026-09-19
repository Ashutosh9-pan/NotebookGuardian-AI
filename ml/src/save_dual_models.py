import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

DATA_FILE = Path("ml/data/dual_label_features.csv")
MODEL_DIR = Path("ml/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

CODE_MODEL_FILE = MODEL_DIR / "code_risk_model.joblib"
EXEC_MODEL_FILE = MODEL_DIR / "execution_risk_model.joblib"
CONFIG_FILE = MODEL_DIR / "dual_model_config.json"

CODE_FEATURES = [
    "source_length",
    "line_count",
    "syntax_valid",
    "num_assignments",
    "num_function_defs",
    "num_class_defs",
    "num_function_calls",
    "num_imports",
    "num_if",
    "num_for",
    "num_while",
    "num_try",
    "num_returns",
    "num_names_loaded",
    "num_names_stored",
    "num_attributes",
    "num_subscripts",
    "num_constants",
    "has_fit",
    "has_predict",
    "has_transform",
    "has_drop",
    "has_remove",
    "has_inplace",
    "has_read_csv",
    "has_read_excel",
    "has_gpu_keyword",
    "has_exception_keyword",
    "has_model_keyword",
]

EXECUTION_FEATURES = [
    "was_executed",
    "execution_count",
    "previous_execution_count",
    "out_of_order",
    "cell_index",
    "source_length",
    "line_count",
    "num_assignments",
    "num_function_calls",
    "num_names_loaded",
    "num_names_stored",
    "num_attributes",
    "has_drop",
    "has_remove",
    "has_inplace",
    "has_fit",
    "has_predict",
    "has_transform",
    "has_read_csv",
    "has_gpu_keyword",
]

# Defaults; replace after tune_dual_thresholds.py if better thresholds are found.
CODE_THRESHOLD = 0.70
EXECUTION_THRESHOLD = 0.60

df = pd.read_csv(DATA_FILE)

def make_model():
    return Pipeline([
        ("scaler", StandardScaler()),
        (
            "classifier",
            LogisticRegression(
                class_weight="balanced",
                max_iter=3000,
                random_state=42,
            ),
        ),
    ])

code_model = make_model()
execution_model = make_model()

print("Training code-risk model...")
code_model.fit(df[CODE_FEATURES], df["code_risk_label"])

print("Training execution-risk model...")
execution_model.fit(df[EXECUTION_FEATURES], df["execution_risk_label"])

joblib.dump(code_model, CODE_MODEL_FILE)
joblib.dump(execution_model, EXEC_MODEL_FILE)

config = {
    "version": "2.0.0",
    "code_threshold": CODE_THRESHOLD,
    "execution_threshold": EXECUTION_THRESHOLD,
    "code_features": CODE_FEATURES,
    "execution_features": EXECUTION_FEATURES,
    "training_rows": int(len(df)),
    "training_cases": int(df["case_name"].nunique()),
}

with open(CONFIG_FILE, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=4)

print("\nDual models saved:")
print(CODE_MODEL_FILE)
print(EXEC_MODEL_FILE)
print(CONFIG_FILE)
