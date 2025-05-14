import os
import urllib.parse
from fastapi import FastAPI, Request
from minio import Minio
from minio.commonconfig import CopySource
from datetime import datetime

print("!!!!!!!!!!=== webhook_receiver.py ===!!!!!!!!!!")


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

    path_map = {
      "FD_csv_EEC": "raw/emploi/",
      "Varmod_EEC_": "metadata/emploi/",
      "notebook": "notebooks/",
      "rna_import": "raw/association/",
      "presidentielle": "raw/election/",
      "crime": "raw/crime/",
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

    return {"status": "ok"}

  except Exception as e:
    print(f"Error processing event: {e}")
    return {"status": "error", "message": str(e)}
