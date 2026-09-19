from huggingface_hub import HfApi, hf_hub_download
from pathlib import Path
import shutil
import time

DATASET_ID = "PELAB-LiU/JunoBench"

OUTPUT_DIR = Path("ml/data/raw/all_cases")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

api = HfApi()
print("Fetching JunoBench file list...")

files = api.list_repo_files(
    repo_id=DATASET_ID,
    repo_type="dataset"
)

cases = {}

for file_name in files:
    if not file_name.startswith("benchmark/"):
        continue

    parts = file_name.split("/")
    if len(parts) < 3:
        continue

    case_name = parts[1]
    cases.setdefault(case_name, {"reproduced": None, "fixed": None})
    filename = parts[-1]

    if filename == f"{case_name}_reproduced.ipynb":
        cases[case_name]["reproduced"] = file_name
    elif filename == f"{case_name}_fixed.ipynb":
        cases[case_name]["fixed"] = file_name

valid_cases = {
    case_name: info
    for case_name, info in cases.items()
    if info["reproduced"] and info["fixed"]
}

print(f"Usable cases found: {len(valid_cases)}")

for index, (case_name, info) in enumerate(sorted(valid_cases.items()), start=1):
    print(f"\n[{index}/{len(valid_cases)}] Downloading {case_name}")

    case_dir = OUTPUT_DIR / case_name
    case_dir.mkdir(parents=True, exist_ok=True)

    for key in ["reproduced", "fixed"]:
        repo_file = info[key]
        destination = case_dir / Path(repo_file).name

        if destination.exists():
            print(f"Already exists: {destination.name}")
            continue

        last_error = None
        for attempt in range(1, 4):
            try:
                downloaded_path = hf_hub_download(
                    repo_id=DATASET_ID,
                    filename=repo_file,
                    repo_type="dataset",
                )
                shutil.copy2(downloaded_path, destination)
                print(f"Saved: {destination.name}")
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                print(f"Attempt {attempt}/3 failed: {exc}")
                if attempt < 3:
                    time.sleep(3)

        if last_error is not None:
            raise last_error

print("\nAll notebook pairs downloaded successfully.")
