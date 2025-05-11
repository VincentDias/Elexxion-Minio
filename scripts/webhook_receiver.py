from fastapi import FastAPI, Request
import json
import os
import logging
from datetime import datetime
import re
from minio import Minio
from minio.error import S3Error

app = FastAPI()

# Configuration des logs
log_dir = "logs/webhook_receiver"
os.makedirs(log_dir, exist_ok=True)
log_filename = datetime.now().strftime("log_webhook_receiver_%Y-%m-%d_%H%M.log")
log_path = os.path.join(log_dir, log_filename)
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Chargement sécurisé des variables d'environnement
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_USER = os.getenv("MINIO_ROOT_USER")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

if not all([MINIO_ENDPOINT, MINIO_USER, MINIO_PASSWORD, MINIO_BUCKET]):
    raise RuntimeError("Une ou plusieurs variables d'environnement MinIO sont manquantes.")

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
        logging.warning("Événement reçu sans clé 'Records'")
        return {"status": "ignored"}
    logging.info("Événement reçu depuis MinIO : %s", json.dumps(event, indent=2))

    for record in event.get("Records", []):
        event_name = record.get("eventName", "")
        if not event_name.startswith("s3:ObjectCreated:"):
            logging.info(f"Événement ignoré (non-creation) : {event_name}")
            continue

        bucket = record.get("s3", {}).get("bucket", {}).get("name", "")
        key = record.get("s3", {}).get("object", {}).get("key", "")

        logging.info(f"Fichier ou dossier détecté : {key}")

        try:
            if (key.endswith('/') or not os.path.splitext(key)[1]) and key.startswith("input/"):
                if re.match(r"^input/FD_csv_EEC\d{2}/?$", key):
                    logging.info(f"Dossier conforme détecté : {key}")
                else:
                    logging.warning(f"Dossier invalide : {key}")

            elif key.startswith("input/"):
                if re.match(r"^input/FD_csv_EEC\d{2}\.csv$", key):
                    dest = key.replace("input/", "datas/emploi/", 1)
                elif re.match(r"^input/Varmod_EEC_\d{4}\.csv$", key):
                    dest = key.replace("input/", "metadatas/emploi/", 1)
                else:
                    logging.warning(f"Fichier inattendu dans le dossier input/ : {key}")
                    continue

                try:
                    client.stat_object(MINIO_BUCKET, dest)
                    logging.warning(f"Le fichier de destination {dest} existe déjà. Aucune action effectuée.")
                except S3Error as e:
                    if hasattr(e, "code") and e.code == "NoSuchKey":
                        client.copy_object(MINIO_BUCKET, dest, f"/{MINIO_BUCKET}/{key}")
                        logging.info(f"Fichier copié vers : {dest}")
                        client.remove_object(MINIO_BUCKET, key)
                        logging.info(f"Fichier source supprimé : {key}")
                    else:
                        raise e

        except S3Error as e:
            logging.error(f"Erreur MinIO lors du traitement de {key} : {str(e)}")
        except Exception as e:
            logging.error(f"Erreur inattendue lors du traitement de {key} : {str(e)}")

    return {"status": "ok"}