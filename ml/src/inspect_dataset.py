from huggingface_hub import HfApi

DATASET_ID = "PELAB-LiU/JunoBench"

api = HfApi()

print("Connecting to JunoBench...")
print(f"Dataset: {DATASET_ID}")
print("-" * 50)

files = api.list_repo_files(
    repo_id=DATASET_ID,
    repo_type="dataset"
)

print(f"Total files found: {len(files)}")
print("\nFirst 20 files:\n")

for file_name in files[:20]:
    print(file_name)
