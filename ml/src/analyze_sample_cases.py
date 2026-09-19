import json
from pathlib import Path
import difflib

BASE_DIR = Path("ml/data/raw/sample_cases")

print("Analyzing sample cases...\n")

for case_dir in sorted(BASE_DIR.iterdir()):
    if not case_dir.is_dir():
        continue

    case_name = case_dir.name
    reproduced_file = case_dir / f"{case_name}_reproduced.ipynb"
    fixed_file = case_dir / f"{case_name}_fixed.ipynb"

    if not reproduced_file.exists() or not fixed_file.exists():
        print(f"{case_name}: missing notebook files")
        continue

    with open(reproduced_file, "r", encoding="utf-8") as f:
        reproduced = json.load(f)

    with open(fixed_file, "r", encoding="utf-8") as f:
        fixed = json.load(f)

    reproduced_cells = [
        "".join(cell.get("source", []))
        for cell in reproduced.get("cells", [])
        if cell.get("cell_type") == "code"
    ]

    fixed_cells = [
        "".join(cell.get("source", []))
        for cell in fixed.get("cells", [])
        if cell.get("cell_type") == "code"
    ]

    changed_cells = 0
    max_cells = max(len(reproduced_cells), len(fixed_cells))

    for i in range(max_cells):
        reproduced_code = reproduced_cells[i] if i < len(reproduced_cells) else ""
        fixed_code = fixed_cells[i] if i < len(fixed_cells) else ""

        if reproduced_code != fixed_code:
            changed_cells += 1

    similarity = difflib.SequenceMatcher(
        None,
        "\n".join(reproduced_cells),
        "\n".join(fixed_cells),
    ).ratio()

    print("=" * 60)
    print(f"Case: {case_name}")
    print(f"Reproduced code cells : {len(reproduced_cells)}")
    print(f"Fixed code cells      : {len(fixed_cells)}")
    print(f"Changed cells         : {changed_cells}")
    print(f"Code similarity       : {similarity * 100:.2f}%")

print("\nAnalysis complete.")
