import os
import urllib.parse
from fastapi import FastAPI, Request
from minio import Minio
from minio.commonconfig import CopySource
from datetime import datetime

print("🏁🏁🏁🏁🏁🏁🏁 webhook.py 🏁🏁🏁🏁🏁🏁🏁")


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
    print("📥​ Event received 📥​")

    if "Records" not in event:
      return {"status": "ignored"}

    path_map = {
      "script": "scripts/",
      "notebook": "notebooks/",
      "FD_csv_EEC": "raw/emploi/",
      "Varmod_EEC_": "metadata/emploi/",
      "rna_import": "raw/association/",
      "presidentielle": "raw/election/",
      "crime": "raw/crime/",
    }

    for record in event.get("Records", []):
      event_name = record.get("eventName", "")
      print(f"​🔃​ Processing event: {event_name}")

      if not event_name.startswith("s3:ObjectCreated:"):
        continue

      key = record.get("s3", {}).get("object", {}).get("key", "")
      key = urllib.parse.unquote(key)
      print(f"📂 File path => {key}")

      if (key.endswith('/') or not os.path.splitext(key)[1]) and key.startswith("input/"):
        continue

      if key.startswith("input/"):
        # Find path in path_map
        path = None
        for keyword, folder in path_map.items():
          if keyword in key:
            path = key.replace("input/", folder, 1)
            break

        if not path:
          print(f"❌ File does not match expected patterns: {key}")
          continue

        # Add timestamp on filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        base, ext = os.path.splitext(path)
        path = f"{base}_{timestamp}{ext}"

        # Check if file already exists
        folder = os.path.dirname(path) + "/"
        # Filename without timestamp
        filename = os.path.basename(key)

        if minio_file_exists(client, MINIO_BUCKET, folder, filename):
          print(f"🙀 A file '{filename}' already exists in {folder} ...")
          client.remove_object(MINIO_BUCKET, key)
          print(f"🔥 File '{filename}' deleted.")
          continue

        # Copy file to new location
        print(f"✅ Copying file to: {path}")
        source = CopySource(MINIO_BUCKET, key)
        client.copy_object(MINIO_BUCKET, path, source)

        # Delete original file in /input
        client.remove_object(MINIO_BUCKET, key)

    return {"status": "ok"}

  except Exception as e:
    print(f"💣 Error processing event: {e}")
    return {"status": "error", "message": str(e)}


def minio_file_exists(client, bucket, folder, filename):
  """
  Vérifie si un fichier avec le même nom de base (hors timestamp) et extension existe déjà dans le dossier cible.
  """
  base_name, ext = os.path.splitext(filename)
  # Get all object in folder target
  found = False
  objects = client.list_objects(bucket, prefix=folder, recursive=True)
  for obj in objects:
    obj_name = os.path.basename(obj.object_name)
    obj_base, obj_ext = os.path.splitext(obj_name)

    # If present delete timestamp at filename end
    if "_" in obj_base:
      obj_base_no_ts = "_".join(obj_base.split("_")[:-1])
    else:
      obj_base_no_ts = obj_base

    if obj_base_no_ts == base_name and obj_ext == ext:
      found = True
      break

  return found


@app.get("/health")
async def health():
  return {"status": "ok"}
