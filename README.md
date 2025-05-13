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

## 📂 Arborescence du projet

```plaintext
elexxion_ELT/
├── datas/
│   ├── emploi/
│   ├── criminalite/
│   └── election/
├── metadatas/
│   ├── emploi/
│   ├── criminalite/
│   └── election/
├── notebooks/
├── logs/
└── output/
    ├── bronze/
    │   ├── emploi/
    │   ├── criminalite/
    │   └── election/
    ├── argent/
    │   ├── emploi/
    │   ├── criminalite/
    │   └── election/
    ├── or/
    │   ├── emploi/
    │   ├── criminalite/
    │   └── election/
    └── platinium/
        ├── emploi/
        ├── criminalite/
        └── election/
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
```

- [MinIO Local](http://localhost:9001)  
- [Webhook Local](http://localhost:8000)  

---

## 🧪 Tester le webhook manuellement

```bash
curl -X POST http://localhost:8000/ -H "Content-Type: application/json" -d '{"test": "ok"}'
```

---

## ⚙️ Fonctionnement du webhook

- Tout fichier ou dossier déposé dans input/ du bucket elexxion-elt déclenche le webhook.
- Si un fichier .csv nommé FD_csv_EECXX.csv est détecté, il est déplacé vers raw/emploi/.
- Si un fichier .csv nommé Varmod_EEC_XXXX.csv est détecté, il est déplacé vers metadata/emploi/.

---

## 🔐 Configuration

Variables d’environnement dans le .env :

``` env
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=password
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET=elexxion-elt
```

---

## ✅ Objectifs à venir

- Détection automatique des erreurs dans les fichiers déposés
- Traitement automatique Bronze → Silver → Gold
- Intégration d’un modèle LightGBM avec tuning Optuna