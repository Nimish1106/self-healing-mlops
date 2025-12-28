# Phase 2: Docker + MLflow Integration

**Self-Healing MLOps Pipeline - Production-Grade Foundation**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![MLflow](https://img.shields.io/badge/MLflow-2.9.2-orange.svg)](https://mlflow.org/)
[![Python](https://img.shields.io/badge/Python-3.10-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-teal.svg)](https://fastapi.tiangolo.com/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [What's in Phase 2](#whats-in-phase-2)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Verification](#verification)
- [Next Steps](#next-steps)

---

📘 For detailed design decisions, setup explanations, and troubleshooting, see:
docs/phase2-details.md

## 🎯 Overview

Phase 2 establishes a **production-grade foundation** for the self-healing MLOps pipeline. This phase focuses on:

- **Reproducibility**: Containerized training ensures consistency across environments
- **Traceability**: Dataset fingerprinting links models to exact data versions
- **Simplicity**: Clean separation of concerns with minimal complexity
- **Reliability**: Production-only model serving with proper health checks

**This is NOT a toy project.** Every design decision prioritizes engineering discipline over feature bloat.

---

## ✨ What's in Phase 2

### Core Capabilities

| Feature | Description | Status |
|---------|-------------|--------|
| **Containerized Training** | Model training runs entirely in Docker | ✅ Complete |
| **Dataset Fingerprinting** | SHA256 hash tracking for data lineage | ✅ Complete |
| **MLflow Integration** | Experiment tracking + Model registry | ✅ Complete |
| **Production Model Serving** | API loads only Production-stage models | ✅ Complete |
| **Prediction Logging** | Minimal logging for future drift detection | ✅ Complete |
| **Health Checks** | Proper container health monitoring | ✅ Complete |


## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose Stack                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐  │
│  │   MLflow     │◄─────┤   Trainer    │      │   API    │  │
│  │   Server     │      │  Container   │      │Container │  │
│  │              │      └──────────────┘      └──────────┘  │
│  │ - Tracking   │              │                    │       │
│  │ - Registry   │              │                    │       │
│  │ - Artifacts  │              ▼                    ▼       │
│  └──────────────┘      ┌─────────────────────────────────┐ │
│         ▲              │      Shared Volumes              │ │
│         │              │  - data/   (datasets)            │ │
│         │              │  - mlflow/ (experiments)         │ │
│         └──────────────│  - models/ (fallback)            │ │
│                        └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

Flow:
1. Trainer: Reads data → Trains model → Logs to MLflow → Promotes to Production
2. API: Loads Production model from MLflow → Serves predictions → Logs inference
```

---

## 📦 Prerequisites

### Required

- **Docker** (20.10+): [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (2.0+): [Install Compose](https://docs.docker.com/compose/install/)
- **Git**: For version control

### Optional

- **curl** or **httpie**: For testing API endpoints
- **jq**: For pretty-printing JSON responses

### Check Your Setup

```bash
docker --version        # Should be 20.10+
docker-compose --version # Should be 2.0+
```

---

## 🚀 Quick Start

### 1️⃣ Clone and Enter Project

```bash
git clone <your-repo-url>
cd self-healing-mlops
git checkout phase-2
```

### 2️⃣ Add Your Dataset

Place the dataset in the `data/` directory:

```bash
# Download "Give Me Some Credit" from Kaggle
# Or use your own credit risk dataset
cp /path/to/cs-training.csv data/
```

### 3️⃣ Start the Stack

```bash
# Start MLflow server
docker-compose up -d mlflow

# Wait for MLflow to be ready (10 seconds)
sleep 10

# Run training (this will take 2-5 minutes)
docker-compose up trainer

# Start API service
docker-compose up -d api
```

### 4️⃣ Verify Everything Works

```bash
# Check MLflow UI
open http://localhost:5000

# Check API
curl http://localhost:8000/health

# Make a test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "RevolvingUtilizationOfUnsecuredLines": 0.766127,
    "age": 45,
    "NumberOfTime30_59DaysPastDueNotWorse": 2,
    "DebtRatio": 0.802982,
    "MonthlyIncome": 9120.0,
    "NumberOfOpenCreditLinesAndLoans": 13,
    "NumberOfTimes90DaysLate": 0,
    "NumberRealEstateLoansOrLines": 6,
    "NumberOfTime60_89DaysPastDueNotWorse": 0,
    "NumberOfDependents": 2
  }'
```

**Expected Response:**
```json
{
  "prediction": 0,
  "probability": 0.23,
  "model_version": "1",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---


## 📁 Project Structure

```
self-healing-mlops/
├── README.md                       # This file
├── docker-compose.yml              # Multi-container orchestration
├── Dockerfile                      # Container definition
├── .dockerignore                   # Files to exclude from builds
├── requirements.txt                # Python dependencies
│
├── data/                           # Datasets (mounted as volume)
│   └── cs-training.csv            # Credit risk dataset
│
├── src/                            # Source code
│   ├── train_model_mlflow.py     # Containerized training script
│   ├── api_mlflow.py              # Production API
│   └── utils/
│       └── dataset_fingerprint.py # Dataset hashing utility
│
├── mlflow/                         # MLflow data (auto-created)
│   ├── mlflow.db                  # Tracking database
│   └── artifacts/                 # Model artifacts
│
└── models/                         # Local model storage (fallback)

```

---

## ✅ Verification

- [ ] MLflow UI accessible at http://localhost:5000
- [ ] At least one experiment visible in MLflow
- [ ] Model registered with "Production" stage
- [ ] Dataset fingerprint logged in experiment parameters
- [ ] API returns 200 on `/health` endpoint
- [ ] API `/model/info` shows Production model
- [ ] Can make successful prediction via `/predict`
- [ ] Prediction is logged in MLflow
- [ ] Services restart without data loss

---

## 🚀 Next Steps

### Phase 3: Monitoring & Drift Detection

**What's coming:**
- Evidently AI integration
- Covariate drift detection
- Population shift monitoring
- Proxy metrics (confidence entropy)
- Delayed label handling

**Prerequisites completed in Phase 2:**
- ✅ Prediction logging
- ✅ Model versioning
- ✅ Experiment tracking
- ✅ Containerized infrastructure

### Immediate Next Actions

1. **Train multiple models** with different parameters
2. **Experiment** with hyperparameters
3. **Understand MLflow UI** thoroughly
4. **Practice** model promotion workflow
5. **Document** your learning

---


## 👤 Author

**Your Name**
- GitHub: [@nimish1106](https://github.com/nimish1106)
- LinkedIn: [Nimish Somani](https://linkedin.com/in/nimishsomani1)

---

## 🙏 Acknowledgments

- Dataset: "Give Me Some Credit" from Kaggle
- MLflow team for excellent tooling
- FastAPI for modern Python APIs

---

**Built with discipline. Deployed with confidence.**
