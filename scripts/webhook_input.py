import glob
import os
import subprocess
import urllib.parse
from datetime import datetime
from fastapi import FastAPI, Request
from minio import Minio
from minio.commonconfig import CopySource

print("!!!!!!!!!!=== webhook_input.py ===!!!!!!!!!!")


app = FastAPI()

# Chargement des variables d'environnement
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_USER = os.getenv("MINIO_ROOT_USER")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

# Connexion au client MinIO
client = Minio(
  MINIO_ENDPOINT,
  access_key=MINIO_USER,
  secret_key=MINIO_PASSWORD,
  secure=False
)

# Répertoire local pour les notebooks exécutés
NOTEBOOK_LOCAL_DIR = "./executed_notebooks"
os.makedirs(NOTEBOOK_LOCAL_DIR, exist_ok=True)

@app.post("/")
async def receive_event(request: Request):
  try:
    event = await request.json()

    if "Records" not in event:
      return {"status": "ignored"}

    path_map = {
      "FD_csv_EEC": "raw/emploi/",
      "Varmod_EEC_": "metadata/emploi/",
      "notebook": "notebooks/",
      "rna_import": "raw/association/",
      "presidentielle": "raw/election/",
      "crime": "raw/crime/",
      "script": "scripts",
    }

    for record in event.get("Records", []):
      event_name = record.get("eventName", "")
      print(f"Processing event: {event_name}")

      if not event_name.startswith("s3:ObjectCreated:"):
        print("Event ignored (not an ObjectCreated event)")
        continue

      key = record.get("s3", {}).get("object", {}).get("key", "")
      key = urllib.parse.unquote(key)
      print(f"Decoded key: {key}")

      if (key.endswith('/') or not os.path.splitext(key)[1]) and key.startswith("input/"):
        print(f"Ignoring folder or invalid file: {key}")
        continue

      if key.startswith("input/"):
        # Find path in path_map
        path = None
        for keyword, folder in path_map.items():
          if keyword in key:
            path = key.replace("input/", folder, 1)
            break

        if not path:
          print(f"File does not match expected patterns: {key}")
          continue

        # Add timestamp on filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        base, ext = os.path.splitext(path)
        path = f"{base}_{timestamp}{ext}"

        # Copy file to new location
        print(f"Copying file to: {path}")
        source = CopySource(MINIO_BUCKET, key)
        client.copy_object(MINIO_BUCKET, path, source)

        # Delete original file in /input
        print(f"Removing original file: {key}")
        client.remove_object(MINIO_BUCKET, key)

        # === NOUVELLE PARTIE : Exécuter le notebook s'il est dans notebooks/ ===
        if path.startswith("notebooks/") and path.endswith(".ipynb"):
          local_path = os.path.join(NOTEBOOK_LOCAL_DIR, os.path.basename(path))
          executed_path = os.path.join(
              NOTEBOOK_LOCAL_DIR, "executed_" + os.path.basename(path)
          )

          print(f"📥 Téléchargement du notebook : {path}")
          client.fget_object(MINIO_BUCKET, path, local_path)

          # Vérifier si le notebook est "association"
          if "association" in os.path.basename(path):
            print(f"⚙️ Exécution spécifique pour le notebook 'association' : {local_path}")
            subprocess.run([
              "jupyter", "nbconvert", "--to", "notebook", "--execute",
              "--ExecutePreprocessor.timeout=600",
              "--ExecutePreprocessor.allow_errors=True",
              "--NotebookApp.iopub_data_rate_limit=10000000",
              "--output", executed_path,
              "--ExecutePreprocessor.kernel_name=python3",
              "--execute", local_path
            ])

            # Copier le fichier Parquet généré dans MinIO
            parquet_dir = "./association/parquet/bronze"
            os.makedirs(parquet_dir, exist_ok=True)
            parquet_files = glob.glob(os.path.join(parquet_dir, "*.parquet"))

            for parquet_file in parquet_files:
              parquet_key = f"output/bronze/association/{os.path.basename(parquet_file)}"
              print(f"📤 Uploading Parquet file to MinIO: {parquet_key}")
              client.fput_object(MINIO_BUCKET, parquet_key, parquet_file)
          else:
            print(f"⚙️ Exécution du notebook générique : {local_path}")
            subprocess.run([
              "jupyter", "nbconvert", "--to", "notebook", "--execute", local_path, "--output", executed_path
            ])

          print(f"✅ Notebook exécuté : {executed_path}")

    return {"status": "ok"}

  except Exception as e:
    print(f"Error processing event: {e}")
    return {"status": "error", "message": str(e)}
