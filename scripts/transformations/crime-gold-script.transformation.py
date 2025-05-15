
from dotenv import load_dotenv
import os
import pandas as pd
import s3fs

load_dotenv()

MINIO_ENDPOINT = "localhost:9000"
MINIO_USER     = os.getenv("MINIO_ROOT_USER")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
BUCKET         = "elexxion-elt"

if not all([MINIO_USER, MINIO_PASSWORD, BUCKET]):
    raise RuntimeError("Définissez MINIO_ROOT_USER, MINIO_ROOT_PASSWORD et MINIO_BUCKET dans le .env")

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


silver_key = f"{BUCKET}/output/silver/crime/df_silver_crime_2016_2024_departement.parquet"
df = pd.read_parquet(f"s3://{silver_key}", storage_options=storage_opts)


df = df.astype({
    "departement": str,
    "region":      int,
    "annee":       int,
    "type":        str,
    "nombre":      int,
    "tpm":         str,
    "population":  int
})


gold_df = (
    df
    .groupby(["departement", "annee", "region", "population"], as_index=False)
    ["nombre"]
    .sum()
)


gold_key = f"{BUCKET}/output/gold/crime/df_gold_crime_2016_2024_departement.parquet"
gold_df.to_parquet(f"s3://{gold_key}", index=False, storage_options=storage_opts)

print(f" Gold Crime généré et stocké : s3://{gold_key}")
