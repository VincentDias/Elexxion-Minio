

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


bronze_prefix = f"{BUCKET}/output/bronze/association"
all_paths     = fs.find(bronze_prefix)
parquet_keys  = [p for p in all_paths if p.lower().endswith(".parquet")]

print(f" {len(parquet_keys)} fichier(s) Bronze trouvé(s) sous {bronze_prefix}")


for key in parquet_keys:
    fname   = os.path.basename(key)
    print(f"▶️ Traitement Silver : {fname}")


    df = pd.read_parquet(f"s3://{key}", storage_options=storage_opts)


    df.columns = (
        df.columns
        .str.lower()
        .str.replace(" ", "_")
    )


    df = df.drop_duplicates()
    df = df.dropna(how="all")


    df = df.rename(columns={
        "adrs_codepostal": "cp",
        "date_publi":      "publication",
        "libcom":          "commune",
        "maj_time":        "maj",
        "objet":           "resume",
        "publication":     "creation",
        "titre":           "nom",
    })


    to_drop = [
        "adr1","adr2","adr3","date_creat","dir_civilite","gestion",
        "groupement","id_ex","nature","objet_social1","objet_social2",
        "observation","position","rup_mi","siret","siteweb"
    ]
    df = df.drop(columns=[c for c in to_drop if c in df.columns])


    silver_key = key.replace("/output/bronze/association/", "/output/silver/association/") \
                    .replace("df_bronze", "df_silver")
    fs.mkdirs(os.path.dirname(silver_key), exist_ok=True)
    df.to_parquet(f"s3://{silver_key}", index=False, storage_options=storage_opts)

    print(f" Silver stocké : s3://{silver_key}")
