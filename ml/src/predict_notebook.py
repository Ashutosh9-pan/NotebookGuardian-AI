import ast
import json
import sys
from pathlib import Path
import joblib
import pandas as pd

MODEL_FILE = Path("ml/models/notebookguardian_model.joblib")
CONFIG_FILE = Path("ml/models/model_config.json")

def safe_execution_count(cell):
    value = cell.get("execution_count")
    return value if isinstance(value, int) else -1

def ast_features(source):
    features = {
        "num_names_loaded": 0,
        "num_names_stored": 0,
        "num_function_defs": 0,
        "num_imports": 0,
        "num_attributes": 0,
        "num_for": 0,
        "num_while": 0,
        "num_if": 0,
        "num_assignments": 0,
        "num_returns": 0,
        "num_constants": 0,
        "num_subscripts": 0,
    }

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return features

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                features["num_names_loaded"] += 1
            elif isinstance(node.ctx, ast.Store):
                features["num_names_stored"] += 1
        elif isinstance(node, ast.FunctionDef):
            features["num_function_defs"] += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            features["num_imports"] += 1
        elif isinstance(node, ast.Attribute):
            features["num_attributes"] += 1
        elif isinstance(node, ast.For):
            features["num_for"] += 1
        elif isinstance(node, ast.While):
            features["num_while"] += 1
        elif isinstance(node, ast.If):
            features["num_if"] += 1
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            features["num_assignments"] += 1
        elif isinstance(node, ast.Return):
            features["num_returns"] += 1
        elif isinstance(node, ast.Constant):
            features["num_constants"] += 1
        elif isinstance(node, ast.Subscript):
            features["num_subscripts"] += 1

    return features

def extract_features(code_cells):
    rows = []

    for cell in code_cells:
        source = "".join(cell.get("source", [])).strip()
        source_lower = source.lower()
        execution_count = safe_execution_count(cell)

        row = {
            "was_executed": int(execution_count != -1),
            "execution_count": execution_count,
            "source_length": len(source),
            "line_count": len(source.splitlines()),
            "num_names_loaded": 0,
            "num_names_stored": 0,
            "num_function_defs": 0,
            "num_imports": 0,
            "num_attributes": 0,
            "num_for": 0,
            "num_while": 0,
            "num_if": 0,
            "num_assignments": 0,
            "num_returns": 0,
            "num_constants": 0,
            "num_subscripts": 0,
            "has_fit": int(".fit(" in source_lower),
            "has_inplace": int("inplace=true" in source_lower),
            "has_gpu_keyword": int("gpu" in source_lower or "cuda" in source_lower),
            "has_read_csv": int("read_csv" in source_lower),
        }

        row.update(ast_features(source))
        rows.append(row)

    return pd.DataFrame(rows)

def risk_level(probability, threshold):
    if probability >= max(0.75, threshold):
        return "HIGH"
    if probability >= threshold:
        return "MEDIUM"
    return "LOW"

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("python ml\\src\\predict_notebook.py <path_to_notebook.ipynb>")
        return

    notebook_path = Path(sys.argv[1])

    if not notebook_path.exists():
        print(f"Notebook not found: {notebook_path}")
        return

    if notebook_path.suffix.lower() != ".ipynb":
        print("Please provide a .ipynb notebook.")
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    threshold = config["threshold"]
    selected_features = config["selected_features"]
    model = joblib.load(MODEL_FILE)

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

    features_df = extract_features(code_cells)[selected_features]
    probabilities = model.predict_proba(features_df)[:, 1]

    print("=" * 75)
    print("NOTEBOOKGUARDIAN ANALYSIS")
    print("=" * 75)
    print(f"\nNotebook      : {notebook_path.name}")
    print(f"Code cells    : {len(code_cells)}")
    print(f"Risk threshold: {threshold}")

    results = []
    for index, probability in enumerate(probabilities, start=1):
        results.append((index, probability, risk_level(probability, threshold)))

    results.sort(key=lambda item: item[1], reverse=True)

    print("\nTop risky cells:\n")
    for cell_number, probability, level in results[:10]:
        print(
            f"Cell #{cell_number:<3} "
            f"Risk: {probability * 100:6.2f}% "
            f"Level: {level}"
        )

    risky_count = sum(
        probability >= threshold
        for _, probability, _ in results
    )

    print("\n" + "-" * 75)
    print(f"Cells above threshold: {risky_count}/{len(code_cells)}")
    print("\nAnalysis complete.")

if __name__ == "__main__":
    main()
