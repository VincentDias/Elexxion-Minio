from dotenv import load_dotenv
import os
import pandas as pd
import re
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

# Recherche des fichiers CSV dans le bucket raw/legislatives
csv_paths = fs.glob(f"{BUCKET}/raw/legislatives/*.csv")
if not csv_paths:
    raise FileNotFoundError("Aucun fichier CSV trouvé dans raw/legislatives/")

for csv_key in csv_paths:
    filename = os.path.basename(csv_key)
    match = re.search(r"(\\d{4})", filename)
    if not match:
        print(f"[!] Année non détectée dans : {filename}")
        continue
    year = match.group(1)

    print(f"▶️ Lecture : {filename}")
    df = pd.read_csv(f"s3://{csv_key}", sep=",", dtype=str, storage_options=storage_opts)

    # Nettoyage des colonnes
    df.columns = df.columns.str.strip().str.replace(" ", "_")
    if "Code_du_département" in df.columns:
        df = df.rename(columns={"Code_du_département": "Code_departement"})
    df["Code_departement"] = df["Code_departement"].astype(str)
    df["Annee"] = year

    # Sauvegarde au format Parquet dans bronze/
    parquet_key = f"{BUCKET}/output/bronze/legislatives/df_bronze_legislatives_{year}.parquet"
    df.to_parquet(f"s3://{parquet_key}", index=False, storage_options=storage_opts)
    print(f"[✓] Bronze stocké : s3://{parquet_key}")