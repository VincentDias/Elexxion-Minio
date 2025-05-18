# 🗳️​ Elexxion_ELT

## SOMMAIRE

- [INTRODUCTION](#-introduction)
- [TECHNOLOGIES](#-technologies)
- [ARBORESCENCE BUCKET](#-arborescence-bucket)
- [ARCHITECTURE](#-architecture)
- [WEBHOOKS](#-webhooks)
- [SCRAPPER](#-scrapper)
- [LANCEMENT RAPIDE](#-lancement-rapide)
- [CONFIGURATION](#-configuration)
- [TO DO](#-to-do)

## 👋 INTRODUCTION

**Elexxion_ELT** est un pipeline d'ingestion, de traitement et d'enrichissement de données destiné à structurer des données thématiques (emploi, criminalité, élection) à des fins d'analyse ou de modélisation. Il repose sur MinIO pour le stockage objet, FastAPI pour le webhook de déclenchement, et LightGBM pour la modélisation.

---

## 🔧 TECHNOLOGIES

- **Docker**
- **Python 3.11**
- **requirements.txt**

---

## 📂 ARBORESCENCE BUCKET

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

## 🧱 ARCHITECTURE

Ce projet repose sur une architecture modulaire basée sur des microservices, chacuns conteneurisés avec Docker :

- **minio client :** configurer l'événement webhook sur le bucket.
- **minio :** service de stockage objet compatible S3.
- **init :** script autonome chargé d’initialiser l’arborescence de dossier du bucket.
- **webhook :** service observant l'état du bucket Minio S3.
- **webhook_aws :** replica automatisé vers AWS S3.
- **scrapper :** service permettant de scrapper récursivement les données d'un repository ou d'une autre provenance.

Chaque composant peut être géré, mis à jour et déployé indépendamment, ce qui favorise la scalabilité, l’automatisation et la résilience.

---

## 🎧​ WEBHOOKS

### /input

- Tout fichier déposé dans le dossier input/ d'elexxion-minio-bucket déclenche le webhook.
- Si la présence d'un fichier est détecté, il est déplacé vers son path dans le bucket.
- Le nom du fichier est préfixé du Timestamp à chaque étape.
- Si un script/notebook est déposé celui-ci est éxécuté avec les données qui lui ont été liées au préalable.

### /aws

- Pipeline de replica vers AWS S3

---

## 🛒 SCRAPPER

Run le service dans le container elexxion-minio (Docker Desktop) afin de scrapper les fichiers de données + scripts/notebooks depuis le repository choisi (.env).

---

## 🔐 CONFIGURATION

Renommer le fichier .env.example en .env puis configurer les variables d'environnement.

---

## ⚡ LANCEMENT RAPIDE

- [MinIO Local](http://localhost:9001)  

```bash
docker compose up --build
```

---

## ✅ TO DO

- Intégration d’un modèle LightGBM avec tuning Optuna (étape de modélisation)
