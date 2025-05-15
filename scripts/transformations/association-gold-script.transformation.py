from dotenv import load_dotenv
import os
import re
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


departement_to_region = {
  '01':'84','02':'32','03':'84','04':'93','05':'93','06':'93',
  '07':'84','08':'44','09':'76','10':'44','11':'76','12':'76',
  '13':'93','14':'28','15':'84','16':'75','17':'75','18':'24',
  '19':'75','2A':'94','2B':'94','21':'27','22':'53','23':'75',
  '24':'75','25':'27','26':'84','27':'28','28':'24','29':'53',
  '30':'76','31':'76','32':'76','33':'75','34':'76','35':'53',
  '36':'24','37':'24','38':'84','39':'27','40':'75','41':'24',
  '42':'84','43':'84','44':'52','45':'24','46':'76','47':'75',
  '48':'76','49':'52','50':'28','51':'44','52':'44','53':'52',
  '54':'44','55':'44','56':'53','57':'44','58':'27','59':'32',
  '60':'32','61':'28','62':'32','63':'84','64':'75','65':'76',
  '66':'76','67':'44','68':'44','69':'84','70':'27','71':'27',
  '72':'52','73':'84','74':'84','75':'11','76':'28','77':'11',
  '78':'11','79':'75','80':'32','81':'76','82':'76','83':'93',
  '84':'93','85':'52','86':'75','87':'75','88':'44','89':'27',
  '90':'27','91':'11','92':'11','93':'11','94':'11','95':'11',
  '971':'01','972':'02','973':'03','974':'04','976':'06'
}
valid_dept = set(departement_to_region.keys())


silver_prefix = f"{BUCKET}/output/silver/association"
all_paths     = fs.find(silver_prefix)
silver_keys   = [p for p in all_paths if p.lower().endswith(".parquet")]
print(f" {len(silver_keys)} fichier(s) Silver trouvé(s) sous {silver_prefix}")


df_list = []
for key in silver_keys:
    df = pd.read_parquet(f"s3://{key}", storage_options=storage_opts)
    df_list.append(df)

if not df_list:
    print(" Aucun fichier Silver à traiter.")
    exit(0)

df = pd.concat(df_list, ignore_index=True)


df["cp"] = df["cp"].astype(str).str.strip()
df = df[df["cp"].str.match(r"^\d{5}$", na=False)]
df["departement"] = df["cp"].str[:2]
df = df[df["departement"].isin(valid_dept)]


df["annee"] = pd.to_datetime(df["maj"], errors="coerce").dt.year
df = df.dropna(subset=["annee"])
df["annee"] = df["annee"].astype(int)


agg = (
    df
    .groupby(["departement", "annee"], as_index=False)
    .size()
    .rename(columns={"size": "nombre_nouvelle_asso"})
)
agg = agg.sort_values(["departement", "annee"])


agg["cumul_global"] = agg.groupby("departement")["nombre_nouvelle_asso"].cumsum()


agg["region"] = agg["departement"].map(departement_to_region)


agg = agg[[
    "departement",
    "region",
    "annee",
    "nombre_nouvelle_asso",
    "cumul_global"
]]


gold_key = f"{BUCKET}/output/gold/association/df_gold_association_departement.parquet"
fs.mkdirs(os.path.dirname(gold_key), exist_ok=True)
agg.to_parquet(f"s3://{gold_key}", index=False, storage_options=storage_opts)

print(f" Gold Association généré et stocké : s3://{gold_key}")
