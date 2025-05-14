from fastapi import FastAPI, Request
import os
import re
from minio import Minio
import urllib.parse
from minio.commonconfig import CopySource

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

@app.post("/")
async def receive_event(request: Request):
  try:
    event = await request.json()
    print(f"Event received: {event}")

    if "Records" not in event:
      print("No 'Records' in event")
      return {"status": "ignored"}

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
        # Emploi
        if re.match(r"^input/FD_csv_EEC\d{2}\.csv$", key):
          dest = key.replace("input/", "raw/emploi/", 1)
        elif re.match(r"^input/Varmod_EEC_\d{4}\.csv$", key):
          dest = key.replace("input/", "metadata/emploi/", 1)

        # Notebooks
        elif "notebook" in key:
          dest = key.replace("input/", "notebooks/", 1)

        # Association
        elif re.match(r"^input/rna_import_\d{8}_dpt_\d{2}\.csv$", key):
          dest = key.replace("input/", "raw/association/", 1)

        # Election
        elif re.match(r"^input/rna_import_\d{8}_dpt_\d{2}\.csv$", key):
          dest = key.replace("input/", "raw/election/", 1)

        # Crime
        elif "crime" in key:
          dest = key.replace("input/", "raw/crime/", 1)

        else:
          print(f"File does not match expected patterns: {key}")
          continue

        print(f"Copying file to: {dest}")
        source = CopySource(MINIO_BUCKET, key)
        client.copy_object(MINIO_BUCKET, dest, source)
        print(f"Removing original file: {key}")
        client.remove_object(MINIO_BUCKET, key)

    return {"status": "ok"}

  except Exception as e:
    print(f"Error processing event: {e}")
    return {"status": "error", "message": str(e)}
