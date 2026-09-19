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
    classification_report,
)

DATA_FILE = "ml/data/advanced_features.csv"
df = pd.read_csv(DATA_FILE)

drop_columns = [
    "case_name",
    "cell_index",
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
print("NOTEBOOKGUARDIAN - ADVANCED LOGISTIC MODEL")
print("=" * 75)

model.fit(X_train, y_train)
predictions = model.predict(X_test)

print(f"\nAccuracy  : {accuracy_score(y_test, predictions):.4f}")
print(f"Precision : {precision_score(y_test, predictions, zero_division=0):.4f}")
print(f"Recall    : {recall_score(y_test, predictions, zero_division=0):.4f}")
print(f"F1 Score  : {f1_score(y_test, predictions, zero_division=0):.4f}")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions))

print("\nClassification Report:")
print(classification_report(y_test, predictions, digits=4, zero_division=0))
