import os
import sys
import importlib.util
from minio import Minio
from dotenv import load_dotenv

load_dotenv()


print("🏁🏁🏁🏁🏁🏁🏁 pipeline.py 🏁🏁🏁🏁🏁🏁🏁")

# Chargement des variables d'environnement
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_USER = os.getenv("MINIO_ROOT_USER")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

# Connexion MinIO
client = Minio(
  MINIO_ENDPOINT,
  access_key=MINIO_USER,
  secret_key=MINIO_PASSWORD,
  secure=False
)

LOCAL_SCRIPT_DIR = "/app/scripts_downloaded"
os.makedirs(LOCAL_SCRIPT_DIR, exist_ok=True)

def run_script_for_category(category: str, raw_path: str):
  print(f"🏁 Start to execute category: {category}")

  # Liste des objets dans scripts/ sur MinIO
  objects = client.list_objects(MINIO_BUCKET, prefix="scripts/", recursive=True)
  matching_scripts = [
    obj.object_name for obj in objects
    if obj.object_name.endswith(".py") and category in obj.object_name
  ]

  if not matching_scripts:
    print(f"❌ No script founded in Minio for '{category}'.")
    return

  for script_key in matching_scripts:
    local_path = os.path.join(LOCAL_SCRIPT_DIR, os.path.basename(script_key))

    try:
      print(f"📥 Downloading {script_key} to {local_path}")
      client.fget_object(MINIO_BUCKET, script_key, local_path)

      print(f"🚀 Running script: {local_path}")
      run_python_script(local_path)
      print(f"✅ Script executed successfully: {script_key}")

    except Exception as e:
      print(f"💥 Error while executing script {script_key}: {e}")

def run_python_script(script_path: str):
  module_name = os.path.splitext(os.path.basename(script_path))[0]
  spec = importlib.util.spec_from_file_location(module_name, script_path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)

if __name__ == "__main__":
  if len(sys.argv) != 3:
    print("❌ Usage attendu : python pipeline.py <category> <raw_path>")
    sys.exit(1)

  category_arg = sys.argv[1]
  raw_path_arg = sys.argv[2]
  run_script_for_category(category_arg, raw_path_arg)
