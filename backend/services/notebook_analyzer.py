import ast
import json
from pathlib import Path

import joblib
import pandas as pd


# ============================================================
# MODEL FILES
# ============================================================

CODE_MODEL_FILE = Path("ml/models/code_risk_model.joblib")
EXECUTION_MODEL_FILE = Path("ml/models/execution_risk_model.joblib")
CONFIG_FILE = Path("ml/models/dual_model_config.json")


# ============================================================
# BASIC HELPERS
# ============================================================

def safe_execution_count(cell):
    value = cell.get("execution_count")
    return value if isinstance(value, int) else -1


def extract_ast_features(source):
    features = {
        "syntax_valid": 1,
        "num_names_loaded": 0,
        "num_names_stored": 0,
        "num_function_defs": 0,
        "num_class_defs": 0,
        "num_function_calls": 0,
        "num_imports": 0,
        "num_attributes": 0,
        "num_for": 0,
        "num_while": 0,
        "num_if": 0,
        "num_try": 0,
        "num_assignments": 0,
        "num_returns": 0,
        "num_constants": 0,
        "num_subscripts": 0,
    }

    try:
        tree = ast.parse(source)
    except SyntaxError:
        features["syntax_valid"] = 0
        return features

    for node in ast.walk(tree):

        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                features["num_names_loaded"] += 1

            elif isinstance(node.ctx, ast.Store):
                features["num_names_stored"] += 1

        elif isinstance(node, ast.FunctionDef):
            features["num_function_defs"] += 1

        elif isinstance(node, ast.ClassDef):
            features["num_class_defs"] += 1

        elif isinstance(node, ast.Call):
            features["num_function_calls"] += 1

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

        elif isinstance(node, ast.Try):
            features["num_try"] += 1

        elif isinstance(
            node,
            (ast.Assign, ast.AnnAssign, ast.AugAssign)
        ):
            features["num_assignments"] += 1

        elif isinstance(node, ast.Return):
            features["num_returns"] += 1

        elif isinstance(node, ast.Constant):
            features["num_constants"] += 1

        elif isinstance(node, ast.Subscript):
            features["num_subscripts"] += 1

    return features


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_features(code_cells):

    rows = []

    previous_execution_count = -1

    for cell_index, cell in enumerate(code_cells, start=1):

        source = "".join(
            cell.get("source", [])
        ).strip()

        source_lower = source.lower()

        execution_count = safe_execution_count(cell)

        was_executed = int(execution_count != -1)

        out_of_order = 0

        if (
            execution_count != -1
            and previous_execution_count != -1
            and execution_count < previous_execution_count
        ):
            out_of_order = 1

        row = {
            # Basic source features
            "source_length": len(source),
            "line_count": len(source.splitlines()),

            # Execution features
            "was_executed": was_executed,
            "execution_count": execution_count,
            "previous_execution_count": previous_execution_count,
            "out_of_order": out_of_order,
            "cell_index": cell_index,

            # Keyword / operation features
            "has_fit": int(".fit(" in source_lower),
            "has_predict": int(".predict(" in source_lower),
            "has_transform": int(".transform(" in source_lower),
            "has_drop": int(".drop(" in source_lower),
            "has_remove": int(".remove(" in source_lower),
            "has_inplace": int("inplace=true" in source_lower),
            "has_read_csv": int("read_csv" in source_lower),
            "has_read_excel": int("read_excel" in source_lower),

            "has_gpu_keyword": int(
                "gpu" in source_lower
                or "cuda" in source_lower
            ),

            "has_exception_keyword": int(
                "exception" in source_lower
                or "error" in source_lower
                or "traceback" in source_lower
            ),

            "has_model_keyword": int(
                "model" in source_lower
                or "classifier" in source_lower
                or "regressor" in source_lower
            ),
        }

        # Add AST features
        row.update(
            extract_ast_features(source)
        )

        rows.append(row)

        if execution_count != -1:
            previous_execution_count = execution_count

    return pd.DataFrame(rows)


# ============================================================
# RISK LEVEL
# ============================================================

def get_risk_level(probability, threshold):

    if probability >= 0.75:
        return "HIGH"

    if probability >= threshold:
        return "MEDIUM"

    return "LOW"


# ============================================================
# RISK REASONS
# ============================================================

def build_reasons(
    source,
    probability,
    threshold
):

    source_lower = source.lower()

    reasons = []

    if ".fit(" in source_lower:
        reasons.append(
            "Model training operation detected"
        )

    if ".predict(" in source_lower:
        reasons.append(
            "Model prediction operation detected"
        )

    if ".transform(" in source_lower:
        reasons.append(
            "Data transformation operation detected"
        )

    if (
        "gpu" in source_lower
        or "cuda" in source_lower
    ):
        reasons.append(
            "GPU/CUDA-specific code detected"
        )

    if "inplace=true" in source_lower:
        reasons.append(
            "In-place data mutation detected"
        )

    if "read_csv" in source_lower:
        reasons.append(
            "External CSV dataset loading detected"
        )

    if "read_excel" in source_lower:
        reasons.append(
            "External Excel dataset loading detected"
        )

    if (
        ".drop(" in source_lower
        or ".remove(" in source_lower
    ):
        reasons.append(
            "Data/state mutation operation detected"
        )

    if not reasons:

        if probability >= threshold:
            reasons.append(
                "Code structure matches patterns "
                "associated with risky notebook cells"
            )
        else:
            reasons.append(
                "No strong risk pattern detected"
            )

    return reasons


# ============================================================
# ANALYZE NOTEBOOK
# ============================================================

def analyze_notebook(notebook_path):

    # --------------------------------------------------------
    # Check model files
    # --------------------------------------------------------

    if not CODE_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Code risk model not found: {CODE_MODEL_FILE}"
        )

    if not EXECUTION_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Execution risk model not found: {EXECUTION_MODEL_FILE}"
        )

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Dual model config not found: {CONFIG_FILE}"
        )

    # --------------------------------------------------------
    # Load config
    # --------------------------------------------------------

    with CONFIG_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:

        config = json.load(f)

    code_threshold = float(
        config.get("code_threshold", 0.70)
    )

    execution_threshold = float(
        config.get("execution_threshold", 0.60)
    )

    # --------------------------------------------------------
    # Load models
    # --------------------------------------------------------

    code_model = joblib.load(
        CODE_MODEL_FILE
    )

    execution_model = joblib.load(
        EXECUTION_MODEL_FILE
    )

    # --------------------------------------------------------
    # Load notebook
    # --------------------------------------------------------

    notebook_path = Path(notebook_path)

    with notebook_path.open(
        "r",
        encoding="utf-8"
    ) as f:

        notebook = json.load(f)

    # --------------------------------------------------------
    # Extract code cells
    # --------------------------------------------------------

    code_cells = [
        cell
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]

    if not code_cells:
        raise ValueError(
            "No code cells were found in this notebook."
        )

    # --------------------------------------------------------
    # Extract features
    # --------------------------------------------------------

    features_df = extract_features(
        code_cells
    )

    # --------------------------------------------------------
    # Feature lists from config
    # --------------------------------------------------------

    code_features = config["code_features"]

    execution_features = config["execution_features"]

    # --------------------------------------------------------
    # Validate features
    # --------------------------------------------------------

    missing_code_features = [
        feature
        for feature in code_features
        if feature not in features_df.columns
    ]

    missing_execution_features = [
        feature
        for feature in execution_features
        if feature not in features_df.columns
    ]

    if missing_code_features:
        raise ValueError(
            "Missing code model features: "
            + ", ".join(missing_code_features)
        )

    if missing_execution_features:
        raise ValueError(
            "Missing execution model features: "
            + ", ".join(missing_execution_features)
        )

    # --------------------------------------------------------
    # Prepare model inputs
    # --------------------------------------------------------

    code_features_df = features_df[
        code_features
    ]

    execution_features_df = features_df[
        execution_features
    ]

    # --------------------------------------------------------
    # Predictions
    # --------------------------------------------------------

    code_probabilities = (
        code_model.predict_proba(
            code_features_df
        )[:, 1]
    )

    execution_probabilities = (
        execution_model.predict_proba(
            execution_features_df
        )[:, 1]
    )

    # --------------------------------------------------------
    # Build cell results
    # --------------------------------------------------------

    cells = []

    high_count = 0
    medium_count = 0
    low_count = 0

    code_high_count = 0
    execution_high_count = 0

    for index, (
        cell,
        code_probability,
        execution_probability
    ) in enumerate(
        zip(
            code_cells,
            code_probabilities,
            execution_probabilities
        ),
        start=1
    ):

        code_probability = float(
            code_probability
        )

        execution_probability = float(
            execution_probability
        )

        # Combined risk
        combined_probability = max(
            code_probability,
            execution_probability
        )

        # Individual levels
        code_level = get_risk_level(
            code_probability,
            code_threshold
        )

        execution_level = get_risk_level(
            execution_probability,
            execution_threshold
        )

        combined_level = get_risk_level(
            combined_probability,
            min(
                code_threshold,
                execution_threshold
            )
        )

        # Counts
        if combined_level == "HIGH":
            high_count += 1

        elif combined_level == "MEDIUM":
            medium_count += 1

        else:
            low_count += 1

        if code_probability >= code_threshold:
            code_high_count += 1

        if execution_probability >= execution_threshold:
            execution_high_count += 1

        # Source
        source = "".join(
            cell.get("source", [])
        ).strip()

        preview = (
            source
            .replace("\n", " ")
            [:180]
        )

        reasons = build_reasons(
            source,
            combined_probability,
            min(
                code_threshold,
                execution_threshold
            )
        )

        cells.append({

            "cell_number": index,

            # Combined risk
            "risk_probability": round(
                combined_probability,
                4
            ),

            "risk_percentage": round(
                combined_probability * 100,
                2
            ),

            "risk_level": combined_level,

            # Code risk
            "code_risk_probability": round(
                code_probability,
                4
            ),

            "code_risk_percentage": round(
                code_probability * 100,
                2
            ),

            "code_risk_level": code_level,

            # Execution risk
            "execution_risk_probability": round(
                execution_probability,
                4
            ),

            "execution_risk_percentage": round(
                execution_probability * 100,
                2
            ),

            "execution_risk_level": execution_level,

            # Notebook metadata
            "execution_count": cell.get(
                "execution_count"
            ),

            "code_preview": preview,

            "reasons": reasons
        })

    # --------------------------------------------------------
    # Sort risky cells
    # --------------------------------------------------------

    cells.sort(
        key=lambda item: item[
            "risk_probability"
        ],
        reverse=True
    )

    # --------------------------------------------------------
    # Threshold
    # --------------------------------------------------------

    combined_threshold = min(
        code_threshold,
        execution_threshold
    )

    risky_cells = [
        cell
        for cell in cells
        if cell["risk_probability"]
        >= combined_threshold
    ]

    # --------------------------------------------------------
    # Overall risk
    # --------------------------------------------------------

    overall_probability = max(
        max(code_probabilities),
        max(execution_probabilities)
    )

    overall_level = get_risk_level(
        float(overall_probability),
        combined_threshold
    )

    # --------------------------------------------------------
    # Return API response
    # --------------------------------------------------------

    return {

        "notebook_name": notebook_path.name,

        "model_version": config.get(
            "version",
            "2.0.0"
        ),

        "threshold": combined_threshold,

        "code_threshold": code_threshold,

        "execution_threshold": execution_threshold,

        "total_code_cells": len(
            code_cells
        ),

        "cells_above_threshold": len(
            risky_cells
        ),

        "summary": {

            "overall_risk_level": overall_level,

            "highest_risk_percentage": round(
                float(overall_probability) * 100,
                2
            ),

            "high_risk_cells": high_count,

            "medium_risk_cells": medium_count,

            "low_risk_cells": low_count,

            "code_risk_cells": code_high_count,

            "execution_risk_cells": execution_high_count
        },

        "top_risky_cells": cells[:10],

        "all_cells": sorted(
            cells,
            key=lambda item: item[
                "cell_number"
            ]
        )
    }