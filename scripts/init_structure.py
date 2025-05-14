import io
import os
from datetime import datetime
from minio import Minio
from minio.error import S3Error

print("!!!!!!!!!!=== init_structure.py ===!!!!!!!!!!")


MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_USER = os.getenv("MINIO_ROOT_USER")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_BUCKET = MINIO_BUCKET.lower()

# Vérification des variables d'environnement
if not MINIO_ENDPOINT:
  raise EnvironmentError("La variable d'environnement MINIO_ENDPOINT n'est pas définie.")

if not MINIO_USER:
  raise EnvironmentError("La variable d'environnement MINIO_ROOT_USER n'est pas définie.")

if not MINIO_PASSWORD:
  raise EnvironmentError("La variable d'environnement MINIO_ROOT_PASSWORD n'est pas définie.")

if not MINIO_BUCKET:
  raise EnvironmentError("La variable d'environnement MINIO_BUCKET n'est pas définie.")


# Connexion au client MinIO
client = Minio(
  MINIO_ENDPOINT,
  access_key=MINIO_USER,
  secret_key=MINIO_PASSWORD,
  secure=False
)

try:
  if client.bucket_exists(MINIO_BUCKET):
    print(f"Bucket '{MINIO_BUCKET}' existe déjà. Suppression en cours...")

    # Supprimer tous les objets dans le bucket avant de le supprimer
    objects = client.list_objects(MINIO_BUCKET, recursive=True)
    for obj in objects:
      client.remove_object(MINIO_BUCKET, obj.object_name)
      print(f"Objet supprimé : {obj.object_name}")

    # Supprimer le bucket
    client.remove_bucket(MINIO_BUCKET)
    print(f"Bucket '{MINIO_BUCKET}' supprimé.")

  # Recréer le bucket
  client.make_bucket(MINIO_BUCKET)
  print(f"Bucket '{MINIO_BUCKET}' recréé.")

  # Arborescence à créer
  folders = [
    "input",
    "logs",
    "logs/init_structure",
    "logs/webhook_receiver",
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
    "raw/emploi"
  ]

  # Création arborescence de dossiers
  for folder in folders:
    folder_path = f"{folder}/"
    try:
      client.put_object(MINIO_BUCKET, folder_path, data=io.BytesIO(b''), length=0)
      print(f"Dossier virtuel créé : {folder_path}")
    except S3Error as e:
      error_message = f"Erreur lors de la création du dossier virtuel '{folder_path}' : {e}"
      print(error_message)

  print("Arborescence initiale terminée.")

except Exception as e:
  print(f"Une erreur inattendue s'est produite : {e}")
  exit(1)
