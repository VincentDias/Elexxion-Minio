from dotenv import load_dotenv
import os
import pandas as pd
import re
import s3fs

load_dotenv()

MINIO_ENDPOINT = "localhost:9000"
MINIO_USER     = os.getenv("MINIO_ROOT_USER")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
BUCKET         = "elexxion-elt"

fs = s3fs.S3FileSystem(
    key=MINIO_USER,
    secret=MINIO_PASSWORD,
    client_kwargs={"endpoint_url": f"http://{MINIO_ENDPOINT}"}
)

storage_opts = {
    "key": MINIO_USER,
    "secret": MINIO_PASSWORD,
    "client_kwargs": {"endpoint_url": f"http://{MINIO_ENDPOINT}"}
}

all_paths = fs.find(f"{BUCKET}/raw/crime")

csv_paths = [
    p for p in all_paths
    if re.search(r"crime_2016_2024_departement.*\.csv$", p)
]
if not csv_paths:
    raise FileNotFoundError("Aucun fichier crime_2016_2024_departement*.csv trouvé sous raw/crime")

csv_key = csv_paths[0]
print("CSV détecté :", csv_key)


df = pd.read_csv(
    f"s3://{csv_key}",
    sep=";",
    dtype=str,
    storage_options=storage_opts
)


parquet_key = (
    f"{BUCKET}/output/bronze/crime/"
    f"df_bronze_crime_2016_2024_departement.parquet"
)
df.to_parquet(
    f"s3://{parquet_key}",
    index=False,
    storage_options=storage_opts
)

print(f" Converti et stocké : s3://{parquet_key}")
