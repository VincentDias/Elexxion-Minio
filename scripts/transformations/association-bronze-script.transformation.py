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
    raise RuntimeError("Veuillez définir MINIO_ROOT_USER, MINIO_ROOT_PASSWORD et MINIO_BUCKET dans le .env")

fs = s3fs.S3FileSystem(
    key=MINIO_USER,
    secret=MINIO_PASSWORD,
    client_kwargs={"endpoint_url": f"http://{MINIO_ENDPOINT}"}
)

expected_fields = 23
delimiter       = ";"
storage_opts    = {
    "key": MINIO_USER,
    "secret": MINIO_PASSWORD,
    "client_kwargs": {"endpoint_url": f"http://{MINIO_ENDPOINT}"}
}

# validation
raw_keys = fs.glob(f"{BUCKET}/raw/association/*.csv")
for key in raw_keys:
    filename      = os.path.basename(key)
    out_key       = key.replace("/raw/association/", "/raw/association/valid/").replace(".csv", "_valid.csv")
    valid_lines   = []
    error_lines   = []
    with fs.open(key, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            if len(line.strip().split(delimiter)) == expected_fields:
                valid_lines.append(line.strip())
            else:
                error_lines.append(i)
    with fs.open(out_key, "w", encoding="utf-8") as f:
        for l in valid_lines:
            f.write(l + "\n")

# conversion
valid_keys = fs.glob(f"{BUCKET}/raw/association/valid/*.csv")
for key in valid_keys:
    filename = os.path.basename(key)
    m = re.search(r"rna_import_(\d{8})_dpt_([0-9]{2}|[0-9]{3}|2A|2B|97[1-9][0-9])", filename)
    if not m:
        continue
    date_str = m.group(1)
    year     = date_str[:4]
    dpt      = m.group(2)
    parquet_key = (
        f"{BUCKET}/output/bronze/association/"
        f"df_bronze_association_{year}_dpt_{dpt}.parquet"
    )
    url_in  = f"s3://{key}"
    url_out = f"s3://{parquet_key}"
    df = pd.read_csv(url_in, sep=delimiter, dtype=str, storage_options=storage_opts)
    df.to_parquet(url_out, index=False, storage_options=storage_opts)
    print(f"Converti et stocké : {url_out}")
