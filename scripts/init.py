import io
import os
from datetime import datetime
from minio import Minio
from minio.error import S3Error

print("🏁🏁🏁🏁🏁🏁🏁 init.py 🏁🏁🏁🏁🏁🏁🏁")


# Chargement des variables d'environnement
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_USER = os.getenv("MINIO_ROOT_USER")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_BUCKET = MINIO_BUCKET.lower()

# Connexion au client MinIO
client = Minio(
  MINIO_ENDPOINT,
  access_key=MINIO_USER,
  secret_key=MINIO_PASSWORD,
  secure=False
)

try:
  if client.bucket_exists(MINIO_BUCKET):
    # Supprimer tous les objets dans le bucket
    objects = client.list_objects(MINIO_BUCKET, recursive=True)
    for obj in objects:
      client.remove_object(MINIO_BUCKET, obj.object_name)

    # Supprimer le bucket
    client.remove_bucket(MINIO_BUCKET)

  # Recréer le bucket
  client.make_bucket(MINIO_BUCKET)
  print(f"✅ New bucket '{MINIO_BUCKET}' created")

  # Arborescence à créer
  folders = [
    "input",
    "metadata/emploi",
    "notebooks",
    "output/bronze/association",
    "output/bronze/crime",
    "output/bronze/election",
    "output/bronze/emploi",
    "output/argent/association",
    "output/argent/crime",
    "output/argent/election",
    "output/argent/emploi",
    "output/or/association",
    "output/or/crime",
    "output/or/election",
    "output/or/emploi",
    "output/platine/association",
    "output/platine/crime",
    "output/platine/election",
    "output/platine/emploi",
    "raw/association",
    "raw/crime",
    "raw/election",
    "raw/emploi",
    "scripts"
  ]

  # Création arborescence de dossiers
  for folder in folders:
    folder_path = f"{folder}/"
    try:
      client.put_object(MINIO_BUCKET, folder_path, data=io.BytesIO(b''), length=0)
      print(f"📂 created folder : {folder_path}")
    except S3Error as e:
      error_message = f"💣 Error during folder creation '{folder_path}' : {e}"
      print(error_message)

  print("✅ Init done.")

except Exception as e:
  print(f"💣 Unexpected error occured : {e}")
  exit(1)
