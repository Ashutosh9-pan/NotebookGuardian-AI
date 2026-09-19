import ast
import json
import sys
from pathlib import Path
import joblib
import pandas as pd

MODEL_DIR = Path("ml/models")
CODE_MODEL_FILE = MODEL_DIR / "code_risk_model.joblib"
EXEC_MODEL_FILE = MODEL_DIR / "execution_risk_model.joblib"
CONFIG_FILE = MODEL_DIR / "dual_model_config.json"

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

def build_rows(code_cells):
    rows = []

    for i, cell in enumerate(code_cells):
        source = "".join(cell.get("source", [])).strip()
        source_lower = source.lower()
        execution_count = safe_execution_count(cell)

        previous_execution_count = -1
        if i > 0:
            previous_execution_count = safe_execution_count(code_cells[i - 1])

        out_of_order = int(
            execution_count != -1
            and previous_execution_count != -1
            and execution_count < previous_execution_count
        )

        row = {
            "cell_index": i + 1,
            "was_executed": int(execution_count != -1),
            "execution_count": execution_count,
            "previous_execution_count": previous_execution_count,
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
            "has_exception_keyword": int(
                "try:" in source_lower or "except " in source_lower
            ),
            "has_model_keyword": int(
                "model" in source_lower
                or "classifier" in source_lower
                or "regressor" in source_lower
            ),
        }

        row.update(ast_features(source))
        rows.append(row)

    return pd.DataFrame(rows)

def level(prob, threshold):
    if prob >= max(0.75, threshold):
        return "HIGH"
    if prob >= threshold:
        return "MEDIUM"
    return "LOW"

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("python ml\\src\\predict_notebook_dual.py <path_to_notebook.ipynb>")
        return

    notebook_path = Path(sys.argv[1])

    if not notebook_path.exists():
        print(f"Notebook not found: {notebook_path}")
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    code_model = joblib.load(CODE_MODEL_FILE)
    execution_model = joblib.load(EXEC_MODEL_FILE)

    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = json.load(f)

    code_cells = [
        cell
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]

    if not code_cells:
        print("No code cells found.")
        return

    feature_df = build_rows(code_cells)

    code_probs = code_model.predict_proba(
        feature_df[config["code_features"]]
    )[:, 1]

    exec_probs = execution_model.predict_proba(
        feature_df[config["execution_features"]]
    )[:, 1]

    rows = []
    for i, (code_prob, exec_prob) in enumerate(zip(code_probs, exec_probs), start=1):
        overall = max(code_prob, exec_prob)
        rows.append({
            "cell": i,
            "code_risk": code_prob,
            "execution_risk": exec_prob,
            "overall": overall,
        })

    rows.sort(key=lambda item: item["overall"], reverse=True)

    print("=" * 85)
    print("NOTEBOOKGUARDIAN DUAL-RISK ANALYSIS")
    print("=" * 85)
    print(f"\nNotebook: {notebook_path.name}")
    print(f"Code cells: {len(code_cells)}")
    print(
        f"Thresholds -> code: {config['code_threshold']}, "
        f"execution: {config['execution_threshold']}"
    )

    print("\nTop risky cells:\n")
    for item in rows[:10]:
        code_level = level(item["code_risk"], config["code_threshold"])
        exec_level = level(item["execution_risk"], config["execution_threshold"])
        print(
            f"Cell #{item['cell']:<3} | "
            f"Code: {item['code_risk'] * 100:6.2f}% ({code_level}) | "
            f"Execution: {item['execution_risk'] * 100:6.2f}% ({exec_level})"
        )

    print("\nAnalysis complete.")

if __name__ == "__main__":
    main()
