import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

DATA_FILE = "ml/data/advanced_features.csv"
df = pd.read_csv(DATA_FILE)

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

X = df[selected_features]
y = df["label"]
groups = df["case_name"]

splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
train_index, test_index = next(splitter.split(X, y, groups=groups))

X_train = X.iloc[train_index]
X_test = X.iloc[test_index]
y_train = y.iloc[train_index]
y_test = y.iloc[test_index]

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

print("=" * 75)
print("NOTEBOOKGUARDIAN - SELECTED FEATURE MODEL")
print("=" * 75)

model.fit(X_train, y_train)
predictions = model.predict(X_test)

print(f"\nAccuracy  : {accuracy_score(y_test, predictions):.4f}")
print(f"Precision : {precision_score(y_test, predictions, zero_division=0):.4f}")
print(f"Recall    : {recall_score(y_test, predictions, zero_division=0):.4f}")
print(f"F1 Score  : {f1_score(y_test, predictions, zero_division=0):.4f}")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions))
print("\nSelected-feature training complete.")
