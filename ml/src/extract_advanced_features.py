import ast
import json
from pathlib import Path
import pandas as pd

BASE_DIR = Path("ml/data/raw/all_cases")
OUTPUT_FILE = Path("ml/data/advanced_features.csv")

rows = []

def get_code_cells(notebook):
    return [
        cell for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]

def safe_execution_count(cell):
    value = cell.get("execution_count")
    return value if isinstance(value, int) else -1

def ast_features(source):
    features = {
        "syntax_valid": 1,
        "num_assignments": 0,
        "num_function_defs": 0,
        "num_class_defs": 0,
        "num_function_calls": 0,
        "num_imports": 0,
        "num_if": 0,
        "num_for": 0,
        "num_while": 0,
        "num_try": 0,
        "num_with": 0,
        "num_returns": 0,
        "num_names_loaded": 0,
        "num_names_stored": 0,
        "num_attributes": 0,
        "num_subscripts": 0,
        "num_constants": 0,
    }

    try:
        tree = ast.parse(source)
    except SyntaxError:
        features["syntax_valid"] = 0
        return features

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            features["num_assignments"] += 1
        elif isinstance(node, ast.FunctionDef):
            features["num_function_defs"] += 1
        elif isinstance(node, ast.ClassDef):
            features["num_class_defs"] += 1
        elif isinstance(node, ast.Call):
            features["num_function_calls"] += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            features["num_imports"] += 1
        elif isinstance(node, ast.If):
            features["num_if"] += 1
        elif isinstance(node, ast.For):
            features["num_for"] += 1
        elif isinstance(node, ast.While):
            features["num_while"] += 1
        elif isinstance(node, ast.Try):
            features["num_try"] += 1
        elif isinstance(node, ast.With):
            features["num_with"] += 1
        elif isinstance(node, ast.Return):
            features["num_returns"] += 1
        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                features["num_names_loaded"] += 1
            elif isinstance(node.ctx, ast.Store):
                features["num_names_stored"] += 1
        elif isinstance(node, ast.Attribute):
            features["num_attributes"] += 1
        elif isinstance(node, ast.Subscript):
            features["num_subscripts"] += 1
        elif isinstance(node, ast.Constant):
            features["num_constants"] += 1

    return features

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
        fixed_execution_count = safe_execution_count(fixed_cell)

        previous_execution_count = -1
        if i > 0 and i - 1 < len(reproduced_cells):
            previous_execution_count = safe_execution_count(reproduced_cells[i - 1])

        source_lower = source.lower()
        was_executed = int(execution_count != -1)

        out_of_order = 0
        if (
            execution_count != -1
            and previous_execution_count != -1
            and execution_count < previous_execution_count
        ):
            out_of_order = 1

        source_changed = int(source != fixed_source)
        execution_changed = int(execution_count != fixed_execution_count)
        label = int(source_changed == 1 or execution_changed == 1)

        code_ast_features = ast_features(source)

        row = {
            "case_name": case_name,
            "cell_index": i + 1,
            "execution_count": execution_count,
            "previous_execution_count": previous_execution_count,
            "was_executed": was_executed,
            "out_of_order": out_of_order,
            "source_length": len(source),
            "line_count": len(source.splitlines()),
            "has_fit": int(".fit(" in source_lower),
            "has_predict": int(".predict(" in source_lower),
            "has_transform": int("transform(" in source_lower),
            "has_drop": int(".drop(" in source_lower),
            "has_remove": int(".remove(" in source_lower),
            "has_inplace": int("inplace=true" in source_lower),
            "has_read_csv": int("read_csv" in source_lower),
            "has_read_excel": int("read_excel" in source_lower),
            "has_gpu_keyword": int("gpu" in source_lower or "cuda" in source_lower),
            "has_train_test_split": int("train_test_split" in source_lower),
            "has_exception_keyword": int(
                "try:" in source_lower or "except " in source_lower
            ),
            "has_model_keyword": int(
                "model" in source_lower
                or "classifier" in source_lower
                or "regressor" in source_lower
            ),
            "source_changed_in_fixed": source_changed,
            "execution_changed_in_fixed": execution_changed,
            "label": label,
        }

        row.update(code_ast_features)
        rows.append(row)

df = pd.DataFrame(rows)
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False)

print("=" * 70)
print("ADVANCED FEATURE EXTRACTION COMPLETE")
print("=" * 70)
print(f"\nCases processed : {df['case_name'].nunique()}")
print(f"Rows created    : {len(df)}")
print(f"Total columns   : {len(df.columns)}")
print(f"Risky cells     : {df['label'].sum()}")
print(f"Normal cells    : {(df['label'] == 0).sum()}")
print("\nSyntax-valid cells:")
print(df["syntax_valid"].value_counts())
print(f"\nSaved to: {OUTPUT_FILE}")
