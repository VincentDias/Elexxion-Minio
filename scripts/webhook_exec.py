import os
import urllib.parse
import subprocess
from fastapi import FastAPI, Request
from minio import Minio

print("🏁🏁🏁🏁🏁🏁🏁 webhook_exec.py 🏁🏁🏁🏁🏁🏁🏁")


app = FastAPI()

# Chargement des variables d'environnement
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

@app.post("/")
async def receive_event(request: Request):
  try:
    event = await request.json()
    print("📥​ Event received 📥​")

    if "Records" not in event:
      return {"status": "ignored"}

    for record in event.get("Records", []):
      event_name = record.get("eventName", "")
      print(f"​🔃​ Processing event: {event_name}")

      if not event_name.startswith("s3:ObjectCreated:"):
        continue

      key = record.get("s3", {}).get("object", {}).get("key", "")
      key = urllib.parse.unquote(key)
      print(f"📂 File path => {key}")

      if (key.endswith('/') or not os.path.splitext(key)[1]) and key.startswith("scripts/"):
        continue

      if key.startswith("scripts/") and key.endswith(".py"):
        local_path = f"/app/{key}"
        print(f"🚀 Script file '{local_path}' was executed 🚀")

        # Télécharge le script depuis MinIO si besoin, ici on suppose qu'il est déjà monté
        try:
          result = subprocess.run(["python", local_path], capture_output=True, text=True)
          print(result.stdout)
          print(result.stderr)

        except Exception as e:
          print(f"💣 Error during execution : {e}")

    return {"status": "ok"}

  except Exception as e:
    print(f"💣 Error processing event : {e}")
    return {"status": "error", "message": str(e)}

@app.get("/health")
async def health():
  return {"status": "ok"}
