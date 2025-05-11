# Initialise et structure le bucket sur Minio
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/init_structure.py ./scripts/init_structure.py

CMD ["python", "scripts/init_structure.py"]
