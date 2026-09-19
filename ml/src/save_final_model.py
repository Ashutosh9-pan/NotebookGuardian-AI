import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

DATA_FILE = Path("ml/data/advanced_features.csv")
MODEL_DIR = Path("ml/models")
MODEL_FILE = MODEL_DIR / "notebookguardian_model.joblib"
CONFIG_FILE = MODEL_DIR / "model_config.json"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

selected_features = [
    "was_executed",
    "execution_count",
    "source_length",
    "line_count",
    "num_names_loaded",
    "num_names_stored",
    "num_function_defs",
    "num_imports",
    "num_attributes",
    "num_for",
    "num_while",
    "num_if",
    "num_assignments",
    "num_returns",
    "num_constants",
    "num_subscripts",
    "has_fit",
    "has_inplace",
    "has_gpu_keyword",
    "has_read_csv",
]

THRESHOLD = 0.55

df = pd.read_csv(DATA_FILE)
X = df[selected_features]
y = df["label"]

print("=" * 70)
print("NOTEBOOKGUARDIAN - FINAL MODEL TRAINING")
print("=" * 70)

model = Pipeline([
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

print("\nTraining final model on all available benchmark data...")
model.fit(X, y)
joblib.dump(model, MODEL_FILE)

config = {
    "model_name": "NotebookGuardian Logistic Regression",
    "version": "1.0.0",
    "threshold": THRESHOLD,
    "selected_features": selected_features,
    "training_rows": int(len(df)),
    "training_cases": int(df["case_name"].nunique()),
    "risky_cells": int((y == 1).sum()),
    "normal_cells": int((y == 0).sum()),
}

with open(CONFIG_FILE, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=4)

print("\n" + "=" * 70)
print("FINAL MODEL SAVED")
print("=" * 70)
print(f"\nModel file  : {MODEL_FILE}")
print(f"Config file : {CONFIG_FILE}")
print(f"Threshold   : {THRESHOLD}")
print("\nModel training and save complete.")
