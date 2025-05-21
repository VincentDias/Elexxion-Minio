import importlib.util
import os
import re
import sys
import time
from minio import Minio
from dotenv import load_dotenv
from minio.error import S3Error

print("🏁🏁🏁🏁🏁🏁🏁 pipeline.py 🏁🏁🏁🏁🏁🏁🏁")


load_dotenv()

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



def wait_for_file_completion(filepath: str, timeout: int = 30) -> bool:
  start = time.time()
  part_file = filepath + '.part.minio'
  while time.time() - start < timeout:
    if os.path.exists(filepath) and not os.path.exists(part_file):
      return True
    time.sleep(0.5)
  return False



def run_script_for_category(category: str, raw_path: str):
  print(f"🏁 Start to execute category: {category}")

  # Bronze
  bronze_pattern = re.compile(
    rf"^scripts/script_elexxion_{category}_bronze_\d{{14}}\.py$"
  )
  run_matching_scripts(category, bronze_pattern, raw_path)

  # Argent
  if has_data_for_category("bronze", category):
    print(f"📂 Bronze data found for category: {category}")
    argent_pattern = re.compile(
      rf"^scripts/script_elexxion_{category}_argent_\d{{14}}\.py$"
    )
    run_matching_scripts(category, argent_pattern, raw_path)
  else:
    print(f"📭 No bronze data found for category: {category}, skipping argent script.")

  # Gold
  if has_data_for_category("argent", category):
    print(f"📂 Argent data found for category: {category}")
    gold_pattern = re.compile(
      rf"^scripts/script_elexxion_{category}_or_\d{{14}}\.py$"
    )
    run_matching_scripts(category, gold_pattern, raw_path)
  else:
    print(f"📭 No argent data found for category: {category}, skipping gold script.")



def run_matching_scripts(category: str, pattern: re.Pattern, raw_path: str):
  try:
    objects = list(client.list_objects(MINIO_BUCKET, prefix="scripts/", recursive=True))
    matching_scripts = [
      obj.object_name for obj in objects
      if pattern.match(obj.object_name)
    ]
  except S3Error as e:
    print(f"💥 MinIO listing error: {e}")
    return

  if not matching_scripts:
    print(f"❌ No matching scripts found in MinIO for pattern: {pattern.pattern}")
    return

  for script_key in matching_scripts:
    local_path = os.path.join(LOCAL_SCRIPT_DIR, os.path.basename(script_key))

    try:
      print(f"📥 Downloading {script_key} to {local_path}")
      client.fget_object(MINIO_BUCKET, script_key, local_path)

      if wait_for_file_completion(local_path, timeout=10):
        print(f"🚀 Running script: {local_path}")
        run_python_script(local_path)
        print(f"✅ Script executed successfully!")
      else:
        print(f"⏱️ Timeout waiting for complete file: {local_path}")

    except Exception as e:
      print(f"💥 Error while executing script {script_key}: {e}")



def run_python_script(script_path: str):
  module_name = os.path.splitext(os.path.basename(script_path))[0]
  spec = importlib.util.spec_from_file_location(module_name, script_path)
  module = importlib.util.module_from_spec(spec)
  try:
    spec.loader.exec_module(module)
  except Exception as e:
    print(f"💥 Error while running {script_path}: {e}")



def has_data_for_category(level: str, category: str) -> bool:
  prefix = f"output/{level}/{category}/"
  try:
    objects = client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=True)
    for _ in objects:
      return True
    return False
  except Exception as e:
    print(f"💥 Error checking {level} data for {category}: {e}")
    return False


if __name__ == "__main__":
  if len(sys.argv) != 3:
    print("❌ Usage attendu : python pipeline.py <category> <raw_path>")
    sys.exit(1)

  category_arg = sys.argv[1]
  raw_path_arg = sys.argv[2]
  run_script_for_category(category_arg, raw_path_arg)
