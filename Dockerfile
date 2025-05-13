# Initialise et structure le bucket sur Minio
FROM python:3.13-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements.txt dans le conteneur
COPY requirements.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier les autres scripts dans le conteneur
COPY scripts/init_structure.py ./scripts/init_structure.py
COPY scripts/scrapper.py ./scripts/scrapper.py

# Exécuter les autres scripts
CMD ["sh", "-c", "python scripts/init_structure.py && python scripts/scrapper.py"]
