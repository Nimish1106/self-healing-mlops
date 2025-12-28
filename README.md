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
- [Detailed Setup](#detailed-setup)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Key Concepts](#key-concepts)
- [Next Steps](#next-steps)

---

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

### Design Principles

1. **Reproducibility First**: Training must produce identical results given same data
2. **No Clever Logic**: Simple, predictable behavior beats flexibility
3. **Clean Separation**: Training → Logging → Serving (no mixing)
4. **Foundation, Not Features**: Build a rock-solid base for Phase 3+

---

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

## 🔧 Detailed Setup

### Step-by-Step Walkthrough

#### 1. Prepare Data Directory

```bash
mkdir -p data
# Add your cs-training.csv to data/
```

#### 2. Start MLflow Tracking Server

```bash
docker-compose up -d mlflow

# Verify MLflow is running
docker-compose logs mlflow

# Access UI
open http://localhost:5000
```

#### 3. Train Your First Model

```bash
# Run containerized training
docker-compose up trainer

# Follow logs
docker-compose logs -f trainer
```

**What happens during training:**
- ✅ Dataset is loaded from `/app/data/cs-training.csv`
- ✅ Dataset fingerprint (SHA256 hash) is computed
- ✅ Model is trained with reproducible random seed
- ✅ All metrics logged to MLflow
- ✅ Model registered in MLflow Registry
- ✅ Model automatically promoted to **Production** stage

#### 4. Verify in MLflow UI

Open http://localhost:5000 and check:
- **Experiments** tab: See your training run
- Click on run: View metrics, parameters, dataset hash
- **Models** tab: See `credit-risk-model` in Production

#### 5. Start API Service

```bash
docker-compose up -d api

# Check API health
curl http://localhost:8000/health
```

#### 6. Test Predictions

```bash
# Get model info
curl http://localhost:8000/model/info

# Make prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @tests/sample_input.json
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

## 📖 Usage Guide

### Training a New Model

```bash
# Method 1: Using docker-compose
docker-compose up trainer

# Method 2: Rebuild if code changed
docker-compose up --build trainer

# Method 3: Run with different parameters
# (Edit src/train_model_mlflow.py first)
docker-compose up --build trainer
```

### Viewing Experiments

```bash
# MLflow UI
open http://localhost:5000

# Navigate to:
# - Experiments → credit-risk-prediction
# - Click on runs to see metrics
# - Models → credit-risk-model
```

### Managing Models

```bash
# Promote a model to Production (via MLflow UI)
# 1. Go to Models tab
# 2. Click on model version
# 3. Click "Stage: None"
# 4. Select "Transition to → Production"

# Or use MLflow CLI (inside container)
docker exec -it mlflow-server mlflow models transition \
  --name credit-risk-model \
  --version 2 \
  --stage Production
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Basic health check |
| `/health` | GET | Detailed health status |
| `/model/info` | GET | Current model metadata |
| `/predict` | POST | Make prediction |

### Making Predictions

```bash
# Using curl
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "RevolvingUtilizationOfUnsecuredLines": 0.5,
    "age": 40,
    "NumberOfTime30_59DaysPastDueNotWorse": 0,
    "DebtRatio": 0.3,
    "MonthlyIncome": 5000.0,
    "NumberOfOpenCreditLinesAndLoans": 5,
    "NumberOfTimes90DaysLate": 0,
    "NumberRealEstateLoansOrLines": 1,
    "NumberOfTime60_89DaysPastDueNotWorse": 0,
    "NumberOfDependents": 1
  }'

# Using httpie (prettier)
http POST localhost:8000/predict < tests/sample_input.json
```

### Viewing Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs trainer
docker-compose logs api
docker-compose logs mlflow

# Follow logs in real-time
docker-compose logs -f api
```

### Managing Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a service
docker-compose restart api

# Rebuild and restart
docker-compose up -d --build

# Remove everything (including volumes)
docker-compose down -v
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

## 🐛 Troubleshooting

### Common Issues

#### 1. MLflow Not Starting

**Symptom:** `docker-compose up mlflow` fails or exits

**Solution:**
```bash
# Check logs
docker-compose logs mlflow

# Remove old volumes and restart
docker-compose down -v
docker-compose up -d mlflow
```

#### 2. Trainer Can't Connect to MLflow

**Symptom:** "Failed to connect to MLflow"

**Solution:**
```bash
# Ensure MLflow is healthy first
docker-compose ps

# Wait longer for MLflow startup
sleep 20
docker-compose up trainer
```

#### 3. API Can't Find Production Model

**Symptom:** "No model in Production stage"

**Solution:**
```bash
# Check if model exists in MLflow UI
open http://localhost:5000

# Manually promote model to Production:
# MLflow UI → Models → credit-risk-model → Version X → Transition to Production

# Or run training again
docker-compose up trainer
```

#### 4. Dataset Not Found

**Symptom:** "FileNotFoundError: data/cs-training.csv"

**Solution:**
```bash
# Verify dataset exists
ls -la data/cs-training.csv

# Check volume mount in docker-compose.yml
docker-compose config | grep data
```

#### 5. Port Already in Use

**Symptom:** "Port 8000 is already allocated"

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill process or change port in docker-compose.yml
# Change: "8000:8000" to "8001:8000"
```

#### 6. Permissions Issues

**Symptom:** "Permission denied" when writing to mlflow/

**Solution:**
```bash
# Fix permissions
sudo chown -R $USER:$USER mlflow/
chmod -R 755 mlflow/
```

### Getting Help

1. **Check logs first:**
   ```bash
   docker-compose logs --tail=100
   ```

2. **Verify service health:**
   ```bash
   docker-compose ps
   curl http://localhost:5000/health
   curl http://localhost:8000/health
   ```

3. **Clean slate restart:**
   ```bash
   docker-compose down -v
   rm -rf mlflow/
   docker-compose up -d mlflow
   sleep 10
   docker-compose up trainer
   docker-compose up -d api
   ```

---

## 💡 Key Concepts

### Dataset Fingerprinting

**Why it matters:** Links each model to the exact data it was trained on.

```python
# Computes SHA256 hash of entire dataset
dataset_hash = "a3f2b8c9d4e5f6..."

# Logged as MLflow parameter
mlflow.log_param("dataset_hash", dataset_hash)
```

**Use case:** If model performance degrades, check if data has changed.

### Production-Only Loading

**Design decision:** API loads ONLY Production models. No fallbacks, no guessing.

**Why:**
- ✅ Clear contract: What's in Production is what gets served
- ✅ Forces proper model promotion workflow
- ✅ Prevents accidental serving of experimental models

**Trade-off:** Requires manual promotion step (automated in Phase 4).

### Prediction Logging

**Purpose:** Capture inference patterns for future drift detection.

```python
# Logs each prediction to MLflow
mlflow.log_metric("probability", 0.23)
```

**Phase 2:** Minimal logging (just predictions)  
**Phase 3:** Will analyze these logs for drift

### Reproducibility

**Guarantees:**
- Same dataset → Same model (via random seed)
- Same Docker image → Same environment
- Same MLflow run ID → Traceable lineage

**How we ensure it:**
- Fixed random seeds (`random_state=42`)
- Pinned dependency versions
- Dataset fingerprinting
- Containerized training

---

## 🎯 Success Criteria

Phase 2 is complete when ALL of these are true:

- [x] Training runs fully inside Docker
- [x] Dataset fingerprint logged for every run
- [x] Multiple experiments visible in MLflow UI
- [x] Model successfully promoted to Production
- [x] API loads Production model reliably
- [x] Predictions logged to MLflow
- [x] Services restart without data loss
- [x] No unnecessary complexity
- [x] Code is clean and well-documented

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

## 📚 Additional Resources

### Documentation
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)

### Learning
- [MLflow Tutorial](https://mlflow.org/docs/latest/tutorials-and-examples/tutorial.html)
- [Docker for Data Science](https://www.docker.com/blog/tag/data-science/)

### Community
- [MLflow GitHub Discussions](https://github.com/mlflow/mlflow/discussions)
- [FastAPI Discord](https://discord.gg/fastapi)

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
