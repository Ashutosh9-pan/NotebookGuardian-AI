import json
from pathlib import Path
import pandas as pd

BASE_DIR = Path("ml/data/raw/sample_cases")
OUTPUT_FILE = Path("ml/data/sample_features.csv")

rows = []

def get_code_cells(notebook):
    return [
        cell for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]

def safe_execution_count(cell):
    count = cell.get("execution_count")
    return count if isinstance(count, int) else -1

for case_dir in sorted(BASE_DIR.iterdir()):
    if not case_dir.is_dir():
        continue

    case_name = case_dir.name
    reproduced_file = case_dir / f"{case_name}_reproduced.ipynb"
    fixed_file = case_dir / f"{case_name}_fixed.ipynb"

    if not reproduced_file.exists() or not fixed_file.exists():
        continue

    with open(reproduced_file, "r", encoding="utf-8") as f:
        reproduced = json.load(f)

    with open(fixed_file, "r", encoding="utf-8") as f:
        fixed = json.load(f)

    reproduced_cells = get_code_cells(reproduced)
    fixed_cells = get_code_cells(fixed)

    max_cells = max(len(reproduced_cells), len(fixed_cells))

    for i in range(max_cells):
        reproduced_cell = reproduced_cells[i] if i < len(reproduced_cells) else {}
        fixed_cell = fixed_cells[i] if i < len(fixed_cells) else {}

        source = "".join(reproduced_cell.get("source", [])).strip()
        fixed_source = "".join(fixed_cell.get("source", [])).strip()

        execution_count = safe_execution_count(reproduced_cell)
        previous_execution_count = -1

        if i > 0 and i - 1 < len(reproduced_cells):
            previous_execution_count = safe_execution_count(reproduced_cells[i - 1])

        was_executed = 1 if execution_count != -1 else 0
        out_of_order = 0

        if (
            execution_count != -1
            and previous_execution_count != -1
            and execution_count < previous_execution_count
        ):
            out_of_order = 1

        source_lower = source.lower()
        source_changed = 1 if source != fixed_source else 0

        rows.append({
            "case_name": case_name,
            "cell_index": i + 1,
            "execution_count": execution_count,
            "previous_execution_count": previous_execution_count,
            "was_executed": was_executed,
            "out_of_order": out_of_order,
            "source_length": len(source),
            "line_count": len(source.splitlines()),
            "has_import": int("import " in source_lower),
            "has_fit": int(".fit(" in source_lower),
            "has_predict": int(".predict(" in source_lower),
            "has_drop": int(".drop(" in source_lower),
            "has_remove": int(".remove(" in source_lower),
            "has_transform": int("transform(" in source_lower),
            "has_split": int("train_test_split" in source_lower),
            "has_dataframe": int(
                "dataframe" in source_lower
                or "pd." in source_lower
                or "df[" in source_lower
            ),
            "has_gpu_keyword": int("gpu" in source_lower or "cuda" in source_lower),
            "source_changed_in_fixed": source_changed,
            "label": source_changed,
        })

df = pd.DataFrame(rows)
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False)

print("Feature extraction complete.")
print(f"Rows created: {len(df)}")
print(f"Risky/fixed cells: {df['label'].sum()}")
print(f"Normal cells: {(df['label'] == 0).sum()}")
print(f"Saved to: {OUTPUT_FILE}")
