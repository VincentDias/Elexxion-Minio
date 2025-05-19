from dotenv import load_dotenv
import os
import pandas as pd
import s3fs

# Chargement des variables d'environnement
load_dotenv()

MINIO_ENDPOINT = "localhost:9000"
MINIO_USER     = os.getenv("MINIO_ROOT_USER")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
BUCKET         = "elexxion-elt"

# Initialisation du système de fichiers S3
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

# Lecture des fichiers bronze
bronze_prefix = f"{BUCKET}/output/bronze/legislatives"
bronze_keys = [p for p in fs.find(bronze_prefix) if p.endswith(".parquet")]

if not bronze_keys:
    print(f"[!] Aucun fichier trouvé dans {bronze_prefix}")
    exit(0)

print(f"▶️ {len(bronze_keys)} fichier(s) Bronze trouvé(s)")

for key in bronze_keys:
    print(f"Traitement Silver : {os.path.basename(key)}")
    df = pd.read_parquet(f"s3://{key}", storage_options=storage_opts)

    # Nettoyage général
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    df = df.drop_duplicates().dropna(how="all")

    # Écriture dans le dossier silver
    silver_key = key.replace("/output/bronze/legislatives/", "/output/silver/legislatives/").replace("df_bronze", "df_silver")
    fs.mkdirs(os.path.dirname(silver_key), exist_ok=True)
    df.to_parquet(f"s3://{silver_key}", index=False, storage_options=storage_opts)

    print(f"[✓] Silver stocké : s3://{silver_key}")