from huggingface_hub import HfApi

DATASET_ID = "PELAB-LiU/JunoBench"

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
    cases.setdefault(
        case_name,
        {
            "original": False,
            "reproduced": False,
            "fixed": False,
            "readme": False,
        },
    )

    filename = parts[-1]

    if filename == f"{case_name}.ipynb":
        cases[case_name]["original"] = True
    elif filename == f"{case_name}_reproduced.ipynb":
        cases[case_name]["reproduced"] = True
    elif filename == f"{case_name}_fixed.ipynb":
        cases[case_name]["fixed"] = True
    elif filename == "README.md":
        cases[case_name]["readme"] = True

valid_cases = [
    case_name
    for case_name, info in cases.items()
    if info["reproduced"] and info["fixed"]
]

print("\nTotal benchmark cases found:", len(cases))
print("Cases with reproduced + fixed notebooks:", len(valid_cases))
print("\nFirst 20 usable cases:\n")

for case_name in valid_cases[:20]:
    print(case_name)
