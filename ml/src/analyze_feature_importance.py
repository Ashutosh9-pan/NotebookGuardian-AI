import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

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
y_train = y.iloc[train_index]

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
print("NOTEBOOKGUARDIAN - FEATURE IMPORTANCE ANALYSIS")
print("=" * 75)

model.fit(X_train, y_train)

classifier = model.named_steps["classifier"]
coefficients = classifier.coef_[0]

importance_df = pd.DataFrame({
    "feature": feature_columns,
    "coefficient": coefficients,
    "absolute_importance": abs(coefficients),
}).sort_values(by="absolute_importance", ascending=False)

print("\nTOP 15 MOST IMPORTANT FEATURES")
print("-" * 75)
print(importance_df.head(15).to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print("\n" + "=" * 75)
print("TOP FEATURES INCREASING RISK")
print("=" * 75)
positive_features = importance_df[
    importance_df["coefficient"] > 0
].sort_values(by="coefficient", ascending=False)
print(positive_features.head(10).to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print("\n" + "=" * 75)
print("TOP FEATURES DECREASING RISK")
print("=" * 75)
negative_features = importance_df[
    importance_df["coefficient"] < 0
].sort_values(by="coefficient")
print(negative_features.head(10).to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print("\n" + "=" * 75)
print("WEAKEST FEATURES")
print("=" * 75)
weak_features = importance_df.sort_values(by="absolute_importance", ascending=True)
print(weak_features.head(10).to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print("\nFeature importance analysis complete.")
