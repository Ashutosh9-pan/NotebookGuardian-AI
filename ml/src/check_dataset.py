import pandas as pd
from pathlib import Path

DATA_FILE = Path("ml/data/full_features.csv")
df = pd.read_csv(DATA_FILE)

print("=" * 60)
print("NOTEBOOKGUARDIAN DATASET QUALITY REPORT")
print("=" * 60)

print(f"\nTotal rows        : {len(df)}")
print(f"Total cases       : {df['case_name'].nunique()}")

normal_count = (df["label"] == 0).sum()
risky_count = (df["label"] == 1).sum()

print("\n--- CLASS DISTRIBUTION ---")
print(f"Normal cells      : {normal_count}")
print(f"Risky cells       : {risky_count}")
print(f"Normal percentage : {normal_count / len(df) * 100:.2f}%")
print(f"Risky percentage  : {risky_count / len(df) * 100:.2f}%")

source_only = (
    (df["source_changed_in_fixed"] == 1)
    & (df["execution_changed_in_fixed"] == 0)
).sum()

execution_only = (
    (df["source_changed_in_fixed"] == 0)
    & (df["execution_changed_in_fixed"] == 1)
).sum()

both_changed = (
    (df["source_changed_in_fixed"] == 1)
    & (df["execution_changed_in_fixed"] == 1)
).sum()

print("\n--- WHY CELLS WERE MARKED RISKY ---")
print(f"Source/code change only : {source_only}")
print(f"Execution change only   : {execution_only}")
print(f"Both changed            : {both_changed}")

print("\n--- EXECUTION SIGNALS ---")
print(f"Never executed cells    : {(df['was_executed'] == 0).sum()}")
print(f"Out-of-order cells      : {(df['out_of_order'] == 1).sum()}")

print("\n--- DATA QUALITY ---")
print(f"Duplicate rows          : {df.duplicated().sum()}")
print(f"Missing values          : {df.isnull().sum().sum()}")

print("\n--- RISKY CELLS BY CASE ---")
risky_by_case = (
    df[df["label"] == 1]
    .groupby("case_name")
    .size()
    .sort_values(ascending=False)
)
print(risky_by_case.head(15))

print("\n" + "=" * 60)
print("QUALITY CHECK COMPLETE")
print("=" * 60)
