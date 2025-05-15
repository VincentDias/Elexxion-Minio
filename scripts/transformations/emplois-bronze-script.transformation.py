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
    raise RuntimeError("Veuillez définir MINIO_ROOT_USER, MINIO_ROOT_PASSWORD et MINIO_BUCKET dans le .env")

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

meta_prefix = f"{BUCKET}/metadata/emploi/emploi/metadata"
all_meta = fs.find(meta_prefix)
meta_files = [p for p in all_meta if p.lower().endswith((".csv", ".json"))]
print(f" {len(meta_files)} fichier(s) de metadata trouvé(s) sous {meta_prefix}")

for key in meta_files:
    filename = os.path.basename(key)
    name, ext = os.path.splitext(filename)
    print(f" Traitement du metadata : {filename}")

    if ext.lower() == ".csv":
        df = pd.read_csv(
            f"s3://{key}",
            sep=";",
            dtype=str,
            storage_options=storage_opts
        )
    else:
        df = pd.read_json(
            f"s3://{key}",
            lines=True,
            dtype=str,
            storage_options=storage_opts
        )

    out_key = f"{BUCKET}/output/bronze/emploi/metadata/{name}.parquet"
    df.to_parquet(
        f"s3://{out_key}",
        index=False,
        storage_options=storage_opts
    )
    print(f" Stocké : s3://{out_key}")
