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
elexxion-bucket/
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

- webhook_api : service FastAPI écoutant les événements webhook.
- minio : service de stockage objet compatible S3.
- init_structure : script autonome chargé d’initialiser l’arborescence du bucket.
- minio client : configure l'événement webhook sur le bucket.

Chaque composant peut être géré, mis à jour et déployé indépendamment, ce qui favorise la scalabilité, l’automatisation et la résilience.

---

## ▶️ Lancement rapide

```bash
docker compose up --build
docker compose build --no-cache
```

```bash
docker rm -f $(docker ps -aq)
docker rmi -f $(docker images -q)
docker volume rm $(docker volume ls -q)
docker network prune -f
docker builder prune -af
```

```bash
docker compose logs -f
docker-compose restart webhook
```

```bash
docker exec -it mc sh
docker exec -it mc bash
```

- [MinIO Local](http://localhost:9001)  

---

## 🧪 Tester le webhook manuellement

```bash
curl -X POST -H "Content-Type: application/json" -d @test_event.json http://localhost:8000/
```

---

## ⚙️ Fonctionnement du webhook

- Tout fichier déposé dans le dossier input/ d'elexxion-bucket déclenche le webhook.
- Si la présence d'un fichier est détecté, il est déplacé vers son path dans le bucket.
- Le nom du fichier est préfixé du Timestamp.

---

## 🔐 Configuration

Renommer le fichier .env.example en .env puis configurer les variables d'environnement.

---

## ✅ Objectifs à venir

- Détection automatique des erreurs dans les fichiers déposés
- Traitement automatique Bronze → Silver → Gold
- Intégration d’un modèle LightGBM avec tuning Optuna
