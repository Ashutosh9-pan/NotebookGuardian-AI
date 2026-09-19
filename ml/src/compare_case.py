import json
from pathlib import Path
import difflib

base_path = Path("ml/data/raw/NBspecific_1")

reproduced_file = base_path / "NBspecific_1_reproduced.ipynb"
fixed_file = base_path / "NBspecific_1_fixed.ipynb"

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

print("Reproduced code cells:", len(reproduced_cells))
print("Fixed code cells:", len(fixed_cells))
print("\n" + "=" * 70)
print("DIFFERENCES")
print("=" * 70 + "\n")

diff = difflib.unified_diff(
    reproduced_cells,
    fixed_cells,
    fromfile="REPRODUCED",
    tofile="FIXED",
    lineterm=""
)

for line in diff:
    print(line)
