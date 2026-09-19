from huggingface_hub import hf_hub_download
from pathlib import Path
import shutil

DATASET_ID = "PELAB-LiU/JunoBench"

sample_cases = [
    "NBspecific_1",
    "NBspecific_2",
    "NBspecific_3",
    "NBspecific_4",
    "NBspecific_5",
]

base_output = Path("ml/data/raw/sample_cases")
base_output.mkdir(parents=True, exist_ok=True)

for case_name in sample_cases:
    print(f"\nDownloading {case_name}...")

    case_dir = base_output / case_name
    case_dir.mkdir(parents=True, exist_ok=True)

    files_to_download = [
        f"benchmark/{case_name}/{case_name}_reproduced.ipynb",
        f"benchmark/{case_name}/{case_name}_fixed.ipynb",
        f"benchmark/{case_name}/README.md",
    ]

    for repo_file in files_to_download:
        downloaded_path = hf_hub_download(
            repo_id=DATASET_ID,
            filename=repo_file,
            repo_type="dataset",
        )

        destination = case_dir / Path(repo_file).name
        shutil.copy2(downloaded_path, destination)
        print(f"Saved: {destination}")

print("\nSample download complete.")
