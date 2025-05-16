import os
import requests
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
  """
  Parcourt récursivement les fichiers du dépôt GitHub en utilisant l'API GitHub
  """
  url = f"{GITHUB_API_BASE}/{path}?ref={GITHUB_BRANCH}"
  response = requests.get(url)
  response.raise_for_status()
  items = response.json()

  files = []
  for item in items:
    if item["name"] in [".gitignore", "README.md"]:
      continue

    if item["type"] == "file" and (item["name"].endswith(".csv") or item["name"].endswith(".ipynb") or item["name"].endswith(".py")):
      files.append(item["path"])
    elif item["type"] == "dir":
      files += list_repo_files(item["path"])
  return files


def upload_file_to_minio(file_path):
  """
  Télécharge un fichier brut depuis GitHub et l'envoie dans le dossier input/ du bucket minio
  """
  raw_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{file_path}"
  response = requests.get(raw_url, stream=True)
  response.raise_for_status()

  file_name = Path(file_path).name
  object_name = f"input/{file_name}"

  print(f"🛒​ Uploading : {object_name}")
  client.put_object(
    bucket_name=MINIO_BUCKET,
    object_name=object_name,
    data=response.raw,
    length=int(response.headers.get('Content-Length', 0)),
    content_type="text/csv"
  )
  print(f"✅ {object_name} file nicely move to /input")


def main():
  print("📦 Get files from GitHub storage...")
  all_csv_files = list_repo_files()
  print(f"✅ {len(all_csv_files)} fichiers CSV trouvés.")

  for file_path in all_csv_files:
    upload_file_to_minio(file_path)


if __name__ == "__main__":
  main()
