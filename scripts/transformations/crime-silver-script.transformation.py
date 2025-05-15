
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
    "key":    MINIO_USER,
    "secret": MINIO_PASSWORD,
    "client_kwargs": {"endpoint_url": f"http://{MINIO_ENDPOINT}"}
}


bronze_key = f"{BUCKET}/output/bronze/crime/df_bronze_crime_2016_2024_departement.parquet"
df = pd.read_parquet(f"s3://{bronze_key}", storage_options=storage_opts)


df.columns = df.columns.str.lower().str.replace(" ", "_")
df = df.drop_duplicates().dropna()


df = df.rename(columns={
    "code_departement":    "departement",
    "code_region":         "region",
    "insee_pop":           "population",
    "indicateur":          "type",
    "taux_pour_mille":     "tpm"
})


df = df.drop(columns=[
    "unite_de_compte",
    "insee_log",
    "insee_pop_millesime",
    "insee_log_millesime"
], errors="ignore")


silver_key = f"{BUCKET}/output/silver/crime/df_silver_crime_2016_2024_departement.parquet"
df.to_parquet(f"s3://{silver_key}", index=False, storage_options=storage_opts)

print(f" Silver Crime généré et stocké : s3://{silver_key}")
