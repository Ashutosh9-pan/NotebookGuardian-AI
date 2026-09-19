import pandas as pd
from pathlib import Path

INPUT_FILE = Path("ml/data/advanced_features.csv")
OUTPUT_FILE = Path("ml/data/dual_label_features.csv")

df = pd.read_csv(INPUT_FILE)

df["code_risk_label"] = df["source_changed_in_fixed"].astype(int)
df["execution_risk_label"] = df["execution_changed_in_fixed"].astype(int)
df["combined_risk_label"] = (
    (df["code_risk_label"] == 1)
    | (df["execution_risk_label"] == 1)
).astype(int)

df.to_csv(OUTPUT_FILE, index=False)

print("=" * 70)
print("NOTEBOOKGUARDIAN - DUAL LABEL DATASET")
print("=" * 70)
print(f"\nTotal rows : {len(df)}")
print(f"Cases      : {df['case_name'].nunique()}")
print("\n--- CODE RISK ---")
print(f"Code-risk cells   : {df['code_risk_label'].sum()}")
print(f"Normal code cells : {(df['code_risk_label'] == 0).sum()}")
print("\n--- EXECUTION RISK ---")
print(f"Execution-risk cells   : {df['execution_risk_label'].sum()}")
print(f"Normal execution cells : {(df['execution_risk_label'] == 0).sum()}")

both = (
    (df["code_risk_label"] == 1)
    & (df["execution_risk_label"] == 1)
).sum()

code_only = (
    (df["code_risk_label"] == 1)
    & (df["execution_risk_label"] == 0)
).sum()

execution_only = (
    (df["code_risk_label"] == 0)
    & (df["execution_risk_label"] == 1)
).sum()

print("\n--- BOTH TYPES ---")
print(f"Code only      : {code_only}")
print(f"Execution only : {execution_only}")
print(f"Both           : {both}")
print(f"\nSaved to: {OUTPUT_FILE}")
