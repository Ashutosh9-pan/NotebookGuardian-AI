import pandas as pd
from sklearn.model_selection import GroupKFold
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

DATA_FILE = "ml/data/full_features.csv"
df = pd.read_csv(DATA_FILE)

drop_columns = [
    "case_name",
    "cell_index",
    "fixed_execution_count",
    "source_changed_in_fixed",
    "execution_changed_in_fixed",
    "label",
]

feature_columns = [col for col in df.columns if col not in drop_columns]

X = df[feature_columns]
y = df["label"]
groups = df["case_name"]

group_kfold = GroupKFold(n_splits=5)
fold_results = []

print("=" * 75)
print("NOTEBOOKGUARDIAN - 5 FOLD GROUP CROSS VALIDATION")
print("=" * 75)

for fold, (train_index, test_index) in enumerate(
    group_kfold.split(X, y, groups=groups),
    start=1,
):
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
                max_iter=2000,
                random_state=42,
            ),
        ),
    ])

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, zero_division=0)
    recall = recall_score(y_test, predictions, zero_division=0)
    f1 = f1_score(y_test, predictions, zero_division=0)

    fold_results.append({
        "fold": fold,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    })

    print(f"\nFold {fold}")
    print("-" * 40)
    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, predictions))

results_df = pd.DataFrame(fold_results)

print("\n" + "=" * 75)
print("CROSS VALIDATION SUMMARY")
print("=" * 75)

for metric in ["accuracy", "precision", "recall", "f1"]:
    mean_value = results_df[metric].mean()
    std_value = results_df[metric].std()
    print(f"{metric.capitalize():<10}: {mean_value:.4f} ± {std_value:.4f}")

print("\nPer-fold results:")
print(results_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
print("\nCross validation complete.")
