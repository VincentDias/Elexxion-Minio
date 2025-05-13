from datetime import datetime
from minio import Minio
from minio.error import S3Error
import io
import logging
import os

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_USER = os.getenv("MINIO_ROOT_USER")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

# Vérification des variables d'environnement
if not MINIO_ENDPOINT:
  raise EnvironmentError("La variable d'environnement MINIO_ENDPOINT n'est pas définie.")

if not MINIO_USER:
  raise EnvironmentError("La variable d'environnement MINIO_ROOT_USER n'est pas définie.")

if not MINIO_PASSWORD:
  raise EnvironmentError("La variable d'environnement MINIO_ROOT_PASSWORD n'est pas définie.")

if not MINIO_BUCKET:
  raise EnvironmentError("La variable d'environnement MINIO_BUCKET n'est pas définie.")

MINIO_BUCKET = MINIO_BUCKET.lower()

# Connexion au client MinIO
client = Minio(
  MINIO_ENDPOINT,
  access_key=MINIO_USER,
  secret_key=MINIO_PASSWORD,
  secure=False
)

print("Script init_structure.py bien lancé")

# Définir le dossier de logs relatif au WORKDIR du conteneur
LOG_DIR = "logs/init_structure"
os.makedirs(LOG_DIR, exist_ok=True)

# Génération du nom de fichier log dynamique
log_filename = datetime.now().strftime("init_%Y-%m-%d_%H%M%S.log")
log_path = os.path.join(LOG_DIR, log_filename)

# Configuration du logger
logging.basicConfig(
  filename=log_path,
  level=logging.INFO,
  format="%(asctime)s | %(levelname)s | %(message)s",
)

# Affiche aussi les logs dans la console pour debug Docker
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
logging.getLogger().addHandler(console_handler)

# Message de démarrage
logging.info("Démarrage de init_structure.py")

# Fonction pour logger les erreurs dans un fichier
def log_error(message):
  date_str = datetime.now().strftime("%Y-%m-%d")
  log_path = f"logs/init_structure/erreur_{date_str}.txt"
  # Assurer que le dossier logs/init_structure/ existe localement
  os.makedirs(os.path.dirname(log_path), exist_ok=True)
  with open(log_path, "a", encoding="utf-8") as f:
      f.write(f"{datetime.now().isoformat()} - {message}\n")

# Création du bucket s’il n'existe pas
try:
  if not client.bucket_exists(MINIO_BUCKET):
    client.make_bucket(MINIO_BUCKET)
    print(f"Bucket '{MINIO_BUCKET}' créé.")
    logging.info(f"Bucket créé : {MINIO_BUCKET}")
  else:
    print(f"Bucket '{MINIO_BUCKET}' existe déjà.")
    logging.info(f"Bucket déjà existant : {MINIO_BUCKET}")
except S3Error as e:
  error_message = f"Erreur lors de la vérification ou création du bucket : {e}"
  print(error_message)
  logging.error(f"Erreur lors de la création du bucket : {e}")

# Arborescence à créer
folders = [
  "input",
  "raw/association",
  "raw/criminalite",
  "raw/election",
  "raw/emploi",
  "metadata/emploi",
  "scripts",
  "notebooks",
  "logs",
  "logs/init_structure",
  "logs/webhook_receiver",
  "output/bronze/association",
  "output/bronze/criminalite",
  "output/bronze/election",
  "output/bronze/emploi",
  "output/argent/association",
  "output/argent/criminalite",
  "output/argent/election",
  "output/argent/emploi",
  "output/or/association",
  "output/or/criminalite",
  "output/or/election",
  "output/or/emploi",
  "output/platine/association",
  "output/platine/criminalite",
  "output/platine/election",
  "output/platine/emploi"
]

# Création des "dossiers" (objets vides avec / à la fin)
for folder in folders:
  folder_path = f"{folder}/"
  try:
    client.put_object(MINIO_BUCKET, folder_path, data=io.BytesIO(b''), length=0)
    print(f"Dossier virtuel créé : {folder_path}")
  except S3Error as e:
    error_message = f"Erreur lors de la création du dossier virtuel '{folder_path}' : {e}"
    print(error_message)
    log_error(error_message)

print("Arborescence initiale terminée.")
