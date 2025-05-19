import os
import requests
from io import BytesIO
from minio import Minio
from pathlib import Path

print("🏁🏁🏁🏁🏁🏁🏁 scrapper.py 🏁🏁🏁🏁🏁🏁🏁")


# MinIO config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_USER = os.getenv("MINIO_ROOT_USER")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

# GitHub Config
GITHUB_USER = os.getenv("GITHUB_USER")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH")
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"

# Connexion au client MinIO
client = Minio(
  MINIO_ENDPOINT,
  access_key=MINIO_USER,
  secret_key=MINIO_PASSWORD,
  secure=False
)


def list_repo_files(path=""):
  url = f"{GITHUB_API_BASE}/{path}?ref={GITHUB_BRANCH}"
  response = requests.get(url)
  response.raise_for_status()
  items = response.json()

  files = []
  for item in items:
    if item["name"] in [".gitignore", "README.md", "requirements.txt"]:
      continue

    if item["type"] == "file" and (
      item["name"].endswith(".csv")
      or item["name"].endswith(".ipynb")
      or item["name"].endswith(".py")
    ):
      files.append(item["path"])
    elif item["type"] == "dir":
      files += list_repo_files(item["path"])
  return files


def detect_content_type(extension: str) -> str:
  if extension == ".csv":
    return "text/csv"
  elif extension == ".py":
    return "text/plain"
  elif extension == ".ipynb":
    return "application/json"
  return "application/octet-stream"


def upload_file_to_minio(file_path):
  raw_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{file_path}"
  response = requests.get(raw_url, stream=True)
  response.raise_for_status()

  buffer = BytesIO(response.content)
  buffer.seek(0)
  data = buffer.read()

  if b"\x00" in data:
    print(f"❌ File '{file_path}' contains null bytes. Ignored.")
    return

  extension = Path(file_path).suffix
  content_type = detect_content_type(extension)

  file_name = Path(file_path).name
  object_name = f"input/{file_name}"

  print(f"🛒​ Uploading '{object_name}' with content-type '{content_type}'")
  buffer.seek(0)
  client.put_object(
    bucket_name=MINIO_BUCKET,
    object_name=object_name,
    data=buffer,
    length=len(data),
    content_type=content_type
  )
  print(f"✅ '{object_name}' file nicely move to /input")


def main():
  print("📦 Get files from GitHub storage...")
  all_files = list_repo_files()
  print(f"✅ {len(all_files)} files found.")

  # At first, we prioritize the files that are not scripts or notebooks
  prioritized = [f for f in all_files if "script" not in f.lower() and "notebook" not in f.lower()]
  delayed = [f for f in all_files if "script" in f.lower() or "notebook" in f.lower()]
  sorted_files = prioritized + delayed

  for file_path in sorted_files:
    upload_file_to_minio(file_path)


if __name__ == "__main__":
  main()
