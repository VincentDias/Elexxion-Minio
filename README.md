# 📦 Elexxion_ELT

**Elexxion_ELT** est un pipeline d'ingestion, de traitement et d'enrichissement de données destiné à structurer des données thématiques (emploi, criminalité, élection) à des fins d'analyse ou de modélisation. Il repose sur MinIO pour le stockage objet, FastAPI pour le webhook de déclenchement, et LightGBM pour la modélisation.

---

## 🔧 Technologies utilisées

- **Python 3.11**
- **FastAPI** : webhook déclenché à l'arrivée de fichiers
- **MinIO** : stockage objet simulant un S3 local
- **Docker & Docker Compose**
- ~~**LightGBM + Optuna** (future étape de modélisation)~~
- **MinIO Client (mc)** pour l'administration du bucket

---

## 📂 Arborescence du bucket

```bash
elexxion-minio-bucket/
├── input/
├── metadata/
│   ├── emploi/
├── notebooks/
├── output/
│   ├── argent/
│   │   ├── association/
│   │   ├── crime/
│   │   ├── election/
│   │   ├── emploi/
│   ├── bronze/
│   │   ├── association/
│   │   ├── crime/
│   │   ├── election/
│   │   ├── emploi/
│   ├── or/
│   │   ├── association/
│   │   ├── crime/
│   │   ├── election/
│   │   ├── emploi/
│   ├── platine/
│   │   ├── association/
│   │   ├── crime/
│   │   ├── election/
│   │   ├── emploi/
├── raw/
│   ├── association/
│   ├── crime/
│   ├── election/
│   └── emploi/
├── scripts/
```

---

## 🧱 Architecture

Ce projet repose sur une architecture modulaire basée sur des microservices, chacun conteneurisé avec Docker :

- **minio client :** configurer l'événement webhook sur le bucket.
- **minio :** service de stockage objet compatible S3.
- **init :** script autonome chargé d’initialiser l’arborescence du bucket.
- **webhook_input :** service observant l'état du folder d'entrée du bucket Minio S3.
- **webhook_aws :** replica automatisé vers AWS S3.
- **scrapper :** container permettant de scrapper récursivement les données d'un repository ou autre serveur.

Chaque composant peut être géré, mis à jour et déployé indépendamment, ce qui favorise la scalabilité, l’automatisation et la résilience.

---

## ▶️ Lancement rapide

- [MinIO Local](http://localhost:9001)  

```bash
docker compose down -v
docker compose up --build

docker compose build --no-cache
```

```bash
docker rm -f $(docker ps -aq)
docker volume rm $(docker volume ls -q)
docker network prune -f
docker builder prune -af
docker rmi -f $(docker images -q)
```

```bash
docker compose logs -f
docker-compose restart webhook
```

```bash
docker exec -it minio_client sh
docker exec -it minio_client bash
```

---

## ⚙️ Fonctionnement des webhook

1. /input

- Tout fichier déposé dans le dossier input/ d'elexxion-minio-bucket déclenche le webhook.
- Si la présence d'un fichier est détecté, il est déplacé vers son path dans le bucket.
- Le nom du fichier est préfixé du Timestamp à chaque étape.

1. /aws

- Pipeline replica AWS S3
- "more explanation"
- "more explanation"

---

## 🔐 Configuration

Renommer le fichier .env.example en .env puis configurer les variables d'environnement.

---

## ✅ Objectifs à venir

- Détection automatique des erreurs dans les fichiers déposés
- Traitement automatique Bronze → Silver → Gold
- Intégration d’un modèle LightGBM avec tuning Optuna
