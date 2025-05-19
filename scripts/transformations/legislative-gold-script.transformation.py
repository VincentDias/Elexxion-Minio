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

# Lecture des fichiers silver
silver_prefix = f"{BUCKET}/output/silver/legislatives"
silver_keys = [p for p in fs.find(silver_prefix) if p.endswith(".parquet")]

if not silver_keys:
    print(f"[!] Aucun fichier Silver détecté dans {silver_prefix}")
    exit(0)

print(f"▶️ {len(silver_keys)} fichier(s) Silver trouvé(s)")

df_list = []
for key in silver_keys:
    df = pd.read_parquet(f"s3://{key}", storage_options=storage_opts)
    df_list.append(df)

df = pd.concat(df_list, ignore_index=True)

# Nettoyage et agrégation
df.columns = df.columns.str.lower().str.strip()
df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
df["code_departement"] = df["code_departement"].astype(str).str.zfill(2)
df = df.dropna(subset=["annee"])
df["annee"] = df["annee"].astype(int)

agg = (
    df
    .groupby(["code_departement", "annee"], as_index=False)
    .size()
    .rename(columns={"size": "nombre_votes"})
    .sort_values(["code_departement", "annee"])
)

# Écriture du fichier gold
gold_key = f"{BUCKET}/output/gold/legislatives/df_gold_legislatives_departement.parquet"
fs.mkdirs(os.path.dirname(gold_key), exist_ok=True)
agg.to_parquet(f"s3://{gold_key}", index=False, storage_options=storage_opts)

print(f"[✓] Gold stocké : s3://{gold_key}")