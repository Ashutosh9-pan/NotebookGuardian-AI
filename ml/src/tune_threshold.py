import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

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

print("=" * 80)
print("NOTEBOOKGUARDIAN - THRESHOLD TUNING")
print("=" * 80)

model.fit(X_train, y_train)
risk_probabilities = model.predict_proba(X_test)[:, 1]

thresholds = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
results = []

for threshold in thresholds:
    predictions = (risk_probabilities >= threshold).astype(int)

    precision = precision_score(y_test, predictions, zero_division=0)
    recall = recall_score(y_test, predictions, zero_division=0)
    f1 = f1_score(y_test, predictions, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_test, predictions).ravel()

    results.append({
        "Threshold": threshold,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "True_Positive": tp,
        "False_Positive": fp,
        "False_Negative": fn,
    })

results_df = pd.DataFrame(results)

print("\nTHRESHOLD COMPARISON")
print("-" * 80)
print(results_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

best_row = results_df.loc[results_df["F1"].idxmax()]

print("\n" + "=" * 80)
print("BEST THRESHOLD BY F1")
print("=" * 80)
print(f"Threshold      : {best_row['Threshold']:.2f}")
print(f"Precision      : {best_row['Precision']:.4f}")
print(f"Recall         : {best_row['Recall']:.4f}")
print(f"F1 Score       : {best_row['F1']:.4f}")
print(f"True Positives : {int(best_row['True_Positive'])}")
print(f"False Positives: {int(best_row['False_Positive'])}")
print(f"False Negatives: {int(best_row['False_Negative'])}")
print("\nThreshold tuning complete.")
