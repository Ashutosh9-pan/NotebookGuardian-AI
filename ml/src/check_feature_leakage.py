import pandas as pd
from pathlib import Path

DATA_FILE = Path("ml/data/full_features.csv")
df = pd.read_csv(DATA_FILE)

print("=" * 70)
print("NOTEBOOKGUARDIAN FEATURE LEAKAGE CHECK")
print("=" * 70)

all_columns = list(df.columns)

print("\nAll columns:\n")
for col in all_columns:
    print("-", col)

leakage_columns = [
    "fixed_execution_count",
    "source_changed_in_fixed",
    "execution_changed_in_fixed",
    "label",
]

metadata_columns = [
    "case_name",
    "cell_index",
]

safe_feature_columns = [
    col
    for col in df.columns
    if col not in leakage_columns + metadata_columns
]

print("\n" + "=" * 70)
print("LEAKAGE / TARGET COLUMNS - DO NOT USE AS MODEL INPUT")
print("=" * 70)
for col in leakage_columns:
    if col in df.columns:
        print("-", col)

print("\n" + "=" * 70)
print("METADATA COLUMNS - KEEP FOR TRACKING, NOT TRAINING")
print("=" * 70)
for col in metadata_columns:
    if col in df.columns:
        print("-", col)

print("\n" + "=" * 70)
print("SAFE CANDIDATE FEATURES")
print("=" * 70)
for col in safe_feature_columns:
    print("-", col)

print("\nTotal safe candidate features:", len(safe_feature_columns))
print("\n" + "=" * 70)
print("CHECK COMPLETE")
print("=" * 70)
