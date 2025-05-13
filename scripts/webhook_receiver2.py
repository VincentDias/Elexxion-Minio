from fastapi import FastAPI, Request
import os
import re
from minio import Minio

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
  event = await request.json()
  if "Records" not in event:
    return {"status": "ignored"}

  for record in event.get("Records", []):
    event_name = record.get("eventName", "")
    if not event_name.startswith("s3:ObjectCreated:"):
      continue

    key = record.get("s3", {}).get("object", {}).get("key", "")

    if (key.endswith('/') or not os.path.splitext(key)[1]) and key.startswith("input/"):
      if re.match(r"^input/FD_csv_EEC\d{2}/?$", key):
        pass
      else:
        pass

    elif key.startswith("input/"):
      if re.match(r"^input/FD_csv_EEC\d{2}\.csv$", key):
        dest = key.replace("input/", "raw/emploi/", 1)
      elif re.match(r"^input/Varmod_EEC_\d{4}\.csv$", key):
        dest = key.replace("input/", "metadata/emploi/", 1)
      else:
        continue

      client.copy_object(MINIO_BUCKET, dest, f"/{MINIO_BUCKET}/{key}")
      client.remove_object(MINIO_BUCKET, key)

  return {"status": "ok"}
