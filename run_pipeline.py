import os
from minio import Minio

def run():
  client = Minio(
    endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ROOT_USER"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
    secure=False
  )

  bucket = "elexxion"
  path_local = "input/FD_csv_EEC23.csv"
  path_minio = "bronze/FD_csv_EEC23.csv"

  if not client.bucket_exists(bucket):
    client.make_bucket(bucket)

  client.fput_object(bucket, path_minio, path_local)
  print(f"[Ingestion] Fichier chargé dans MinIO : {path_minio}")
