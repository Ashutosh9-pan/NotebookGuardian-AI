import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score

DATA_FILE = "ml/data/dual_label_features.csv"
df = pd.read_csv(DATA_FILE)

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

groups = df["case_name"]
splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
train_index, test_index = next(
    splitter.split(df, df["combined_risk_label"], groups=groups)
)

thresholds = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]

def evaluate(name, features, target):
    X_train = df.iloc[train_index][features]
    X_test = df.iloc[test_index][features]
    y_train = df.iloc[train_index][target]
    y_test = df.iloc[test_index][target]

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

    model.fit(X_train, y_train)
    probabilities = model.predict_proba(X_test)[:, 1]

    rows = []
    for threshold in thresholds:
        predictions = (probabilities >= threshold).astype(int)
        rows.append({
            "Threshold": threshold,
            "Precision": precision_score(y_test, predictions, zero_division=0),
            "Recall": recall_score(y_test, predictions, zero_division=0),
            "F1": f1_score(y_test, predictions, zero_division=0),
        })

    result = pd.DataFrame(rows)
    best = result.loc[result["F1"].idxmax()]

    print("\n" + "=" * 75)
    print(name)
    print("=" * 75)
    print(result.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print(
        f"\nBest threshold: {best['Threshold']:.2f} | "
        f"Precision: {best['Precision']:.4f} | "
        f"Recall: {best['Recall']:.4f} | "
        f"F1: {best['F1']:.4f}"
    )

evaluate("CODE RISK THRESHOLD TUNING", CODE_FEATURES, "code_risk_label")
evaluate("EXECUTION RISK THRESHOLD TUNING", EXECUTION_FEATURES, "execution_risk_label")
