import json
from pathlib import Path

BASE_DIR = Path("ml/data/raw/sample_cases")

print("Inspecting execution state...\n")

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

    reproduced_code_cells = [
        cell for cell in reproduced.get("cells", [])
        if cell.get("cell_type") == "code"
    ]

    fixed_code_cells = [
        cell for cell in fixed.get("cells", [])
        if cell.get("cell_type") == "code"
    ]

    print("=" * 80)
    print(f"CASE: {case_name}")
    print("=" * 80)

    max_cells = max(len(reproduced_code_cells), len(fixed_code_cells))

    for i in range(max_cells):
        reproduced_cell = reproduced_code_cells[i] if i < len(reproduced_code_cells) else {}
        fixed_cell = fixed_code_cells[i] if i < len(fixed_code_cells) else {}

        reproduced_count = reproduced_cell.get("execution_count")
        fixed_count = fixed_cell.get("execution_count")

        reproduced_source = "".join(reproduced_cell.get("source", [])).strip()
        fixed_source = "".join(fixed_cell.get("source", [])).strip()

        source_changed = reproduced_source != fixed_source
        execution_changed = reproduced_count != fixed_count

        if source_changed or execution_changed:
            print(f"\nCode Cell #{i + 1}")
            print(f"Reproduced execution count : {reproduced_count}")
            print(f"Fixed execution count      : {fixed_count}")
            print(f"Reproduced executed?        : {reproduced_count is not None}")
            print(f"Fixed executed?             : {fixed_count is not None}")
            print(f"Source changed?             : {source_changed}")
            print(f"Execution changed?          : {execution_changed}")
            print("-" * 80)

print("\nExecution-state inspection complete.")
