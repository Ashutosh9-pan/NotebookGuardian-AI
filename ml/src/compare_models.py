import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
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

splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
train_index, test_index = next(splitter.split(X, y, groups=groups))

X_train = X.iloc[train_index]
X_test = X.iloc[test_index]
y_train = y.iloc[train_index]
y_test = y.iloc[test_index]

models = {
    "Logistic Regression": Pipeline([
        ("scaler", StandardScaler()),
        (
            "classifier",
            LogisticRegression(
                class_weight="balanced",
                max_iter=2000,
                random_state=42,
            ),
        ),
    ]),
    "Random Forest": RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    ),
    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=3,
        random_state=42,
    ),
}

print("=" * 75)
print("NOTEBOOKGUARDIAN - MODEL COMPARISON")
print("=" * 75)

results = []

for model_name, model in models.items():
    print("\n" + "-" * 75)
    print(f"Training: {model_name}")
    print("-" * 75)

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, zero_division=0)
    recall = recall_score(y_test, predictions, zero_division=0)
    f1 = f1_score(y_test, predictions, zero_division=0)

    results.append({
        "Model": model_name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
    })

    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions))

results_df = pd.DataFrame(results).sort_values(by="F1", ascending=False)

print("\n" + "=" * 75)
print("FINAL COMPARISON")
print("=" * 75)
print(results_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
print("\nBest model by F1 Score:")
print(results_df.iloc[0]["Model"])
print("\nComparison complete.")
