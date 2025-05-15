# scripts/transformations/election-bronze-script.transformation.py

from dotenv import load_dotenv
import os
import re
import s3fs
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, current_timestamp

load_dotenv()

MINIO_ENDPOINT = "localhost:9000"
MINIO_USER     = os.getenv("MINIO_ROOT_USER")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
BUCKET         = "elexxion-elt"

if not all([MINIO_USER, MINIO_PASSWORD, BUCKET]):
    raise RuntimeError(
        "Veuillez définir MINIO_ROOT_USER, MINIO_ROOT_PASSWORD et MINIO_BUCKET dans le .env"
    )

fs = s3fs.S3FileSystem(
    key=MINIO_USER,
    secret=MINIO_PASSWORD,
    client_kwargs={"endpoint_url": f"http://{MINIO_ENDPOINT}"}
)

raw_prefix = f"{BUCKET}/raw/election"
all_paths  = fs.find(raw_prefix)
csv_keys   = [p for p in all_paths if p.lower().endswith(".csv")]
print(f"▶️ {len(csv_keys)} fichier(s) CSV trouvé(s) sous {raw_prefix}")

spark = (
    SparkSession.builder
    .appName("Election Bronze Pipeline")
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.178"
    )
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.access.key", MINIO_USER)
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_PASSWORD)
    .config("spark.hadoop.fs.s3a.endpoint", f"http://{MINIO_ENDPOINT}")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .getOrCreate()
)

for key in csv_keys:
    filename = os.path.basename(key)
    m = re.search(r"(\d{4}).*(T1|T2|1erTour)", filename, flags=re.IGNORECASE)
    if not m:
        print(f"⚠️ Ignoré (pattern inconnu) : {filename}")
        continue

    year = m.group(1)
    tour = m.group(2).upper().replace("1ERTOUR", "T1")
    print(f"▶️ Traitement : {filename} → année={year}, tour={tour}")

    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(f"s3a://{key}")
        .withColumn("ingestion_date", current_timestamp())
        .withColumn("annee", lit(year))
        .withColumn("tour", lit(tour))
    )

    out_path = (
        f"s3a://{BUCKET}/output/bronze/election/"
        f"election_{year}_{tour}.parquet"
    )
    df.coalesce(1).write.mode("overwrite").parquet(out_path)
    print(f"✅ Écrit en bronze : {out_path}")

spark.stop()
