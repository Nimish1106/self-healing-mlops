# Self-Healing MLOps Pipeline - Complete Tech Stack

## 📋 Overview

A production-grade ML system that monitors model performance, detects drift, and automatically retrains when needed. Built with modern MLOps tools and best practices.

---

## 🏗️ Core Stack

### **Programming & Data**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.10+ | Core application language |
| **Data Processing** | pandas | 2.2.0 | DataFrames and data manipulation |
| **Numerical Computing** | NumPy | 1.26.0 | Array operations and math |
| **Scientific Computing** | SciPy | 1.11.4 | Statistical functions |

### **Machine Learning**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **ML Framework** | scikit-learn | 1.4.0 | Logistic Regression for credit risk |
| **Model Tracking** | MLflow | 2.9.2 | Experiment tracking + model registry |
| **Model Jobs** | joblib | 1.3.2 | Model serialization and pickling |

### **API & Web**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | FastAPI | 0.103.2 | High-performance REST API |
| **ASGI Server** | Uvicorn | 0.23.2 | Async HTTP server |
| **Data Validation** | Pydantic | 1.10.13 | Request/response validation |
| **HTTP Client** | httpx | 0.24.1 | API testing and requests |
| **HTTP Requests** | requests | 2.31.0 | HTTP library |

### **Monitoring & Drift Detection**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Drift Detection** | Evidently AI | 0.4.15 | Statistical drift monitoring |
| **Visualization** | Plotly | 5.18.0 | Interactive drift reports and dashboards |
| **Schema Validation** | Pandera | - | Data type and constraint validation |

### **Orchestration**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Workflow Orchestration** | Apache Airflow | 2.7.3 | DAG-based retraining pipeline |
| **Docker Provider** | airflow-providers-docker | 3.8.0 | Docker task execution in Airflow |
| **Scheduler** | SimpleScheduler (Custom) | - | Monitoring job scheduler (5-min interval) |

---

## 💾 Storage & Database

### **Relational Database**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Database** | PostgreSQL | 13+ | MLOps database for predictions, labels, decisions |
| **DB Driver** | psycopg2-binary | 2.9.9 | Python PostgreSQL adapter |
| **ORM** | SQLAlchemy | 1.4.51 | SQL toolkit and ORM |

### **File Storage**
| Component | Type | Location | Purpose |
|-----------|------|----------|---------|
| **Predictions** | CSV (Append-only) | `monitoring/predictions/predictions.csv` | All production predictions |
| **Labels** | CSV (Append-only) | `monitoring/labels/labels.csv` | Ground truth feedback |
| **Reference Data** | CSV (IMMUTABLE) | `monitoring/reference/reference_data.csv` | Frozen baseline for drift detection |
| **Monitoring Results** | JSON | `monitoring/metrics/monitoring_results/` | Drift/metrics analysis |
| **Drift Reports** | HTML | `monitoring/reports/drift_reports/` | Interactive drift visualizations |
| **Training Data** | CSV | `data/cs-training.csv` | Credit risk training data |

### **MLflow Storage**
| Component | Storage | Purpose |
|-----------|---------|---------|
| **Experiments** | SQLite + Filesystem | Training runs and parameters |
| **Model Registry** | MLflow server | Model versions and stages |
| **Artifacts** | `mlflow/artifacts/` | Trained models and metrics |

### **PostgreSQL Tables**
```
✅ prediction_logs          - All predictions with features
✅ label_store              - Ground truth labels (async)
✅ model_metadata           - Model versions and deployment info
✅ monitoring_metrics       - Proxy metrics and drift detection results
✅ retraining_decisions     - Retraining decisions and gate results
✅ monitoring_alerts        - Drift alerts and notifications
```

---

## 🧪 Testing & Quality

### **Testing**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Test Framework** | pytest | 7.4.3 | Unit and integration tests |
| **Test Timeout** | pytest-timeout | 2.1.0 | Prevent hanging tests |
| **Fixtures** | conftest.py | - | Shared test fixtures |

### **Code Quality**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Code Formatter** | Black | 23.11.0 | Code formatting enforcement |
| **Linter** | Flake8 | 6.1.0 | Code style validation |
| **Type Checker** | MyPy | 1.7.1 | Static type checking |
| **Coverage** | coverage | - | Test coverage reporting |

### **Pre-commit Hooks**
| Hook | Technology | Version | Purpose |
|------|-----------|---------|---------|
| **Hook Manager** | pre-commit | 4.5.0 | Git hooks automation |
| **Hooks Used** | Black, Flake8, MyPy, YAML | - | Auto-format and validate on commit |

---

## 🐳 Containerization & Deployment

### **Container Platform**
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Container Runtime** | Docker | 20.10+ | Application containerization |
| **Orchestration** | Docker Compose | 2.0+ | Multi-container orchestration |

### **Docker Services**
```
🏗️ SERVICE ARCHITECTURE:
├── postgres               - Airflow metadata database
├── postgres-mlops         - MLOps application database (Port 5433)
├── mlflow                 - Model tracking server (Port 5000)
├── airflow-webserver      - Airflow UI (Port 8080)
├── airflow-scheduler      - DAG execution engine
├── trainer                - Model training container
├── bootstrap              - Reference data initialization
├── api                    - FastAPI prediction service (Port 8000)
├── monitoring             - Drift detection scheduler
└── pgadmin                - PostgreSQL UI (Port 5050)
```

### **Network & Volumes**
| Type | Name | Purpose |
|------|------|---------|
| **Network** | mlops-network | Docker bridge network for inter-container communication |
| **Volume** | postgres-db-volume | Airflow PostgreSQL persistence |
| **Volume** | postgres-mlops-volume | MLOps database persistence |
| **Volume** | airflow-mlflow-cache | MLflow cache for Airflow |
| **Mounts** | ./mlflow | MLflow artifacts storage |
| **Mounts** | ./monitoring | Monitoring outputs |
| **Mounts** | ./data | Training data |

---

## 🔄 CI/CD Pipeline

### **Version Control & CI/CD**
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Version Control** | Git | Source code management |
| **CI/CD Platform** | GitHub Actions | Automated testing and deployment |
| **Trigger** | Push to master/develop | Automated workflow execution |

### **GitHub Actions Stages**
```
7-Stage Pipeline:
├─ Stage 0: Pre-commit checks (Black, Flake8, MyPy, YAML)
├─ Stage 1: Data validation (Pandera schemas)
├─ Stage 2: Code quality (Black, Flake8, MyPy - parallel)
├─ Stage 3: Unit tests (pytest with coverage)
├─ Stage 4: Integration tests
├─ Stage 5: Model training & validation
├─ Stage 6: Docker build
└─ Stage 7: Deploy (master branch only)
```

---

## 📊 Architecture Components

### **Core Microservices**
| Service | Type | Port | Purpose |
|---------|------|------|---------|
| **API** | FastAPI | 8000 | REST predictions endpoint |
| **MLflow** | Tracking Server | 5000 | Experiment tracking + registry |
| **Airflow** | Workflow Engine | 8080 | DAG scheduling and execution |
| **Monitoring** | Custom Scheduler | Internal | 5-min drift detection |

### **Orchestration Strategy**
```
DUAL ORCHESTRATION MODEL:
├─ Monitoring Scheduler (SimpleScheduler)
│  ├── Type: Python-based cron scheduler
│  ├── Container: monitoring-scheduler
│  ├── Frequency: Every 5 minutes
│  └── Tasks: Drift detection, proxy metrics
│
└─ Airflow DAG (retraining_pipeline)
   ├── Type: Airflow workflow engine
   ├── Container: airflow-scheduler
   ├── Frequency: Weekly + drift-triggered + manual
   └── Tasks: Shadow training, evaluation gate, promotion
```

### **Data Flow Architecture**
```
INPUT LAYER:
  User Requests → FastAPI → Production Model → Predictions

LOGGING LAYER:
  Predictions → Prediction Logger → CSV + PostgreSQL

MONITORING LAYER (Every 5 min):
  Monitoring Scheduler → Load Predictions → Drift Detection → PostgreSQL

RETRAINING LAYER (Weekly/On-Demand):
  Airflow DAG → Check Conditions → Train Shadow → Evaluate → Gate → Promote

STORAGE LAYER:
  PostgreSQL (transactional) + CSV (audit trail) + MLflow (models)
```

---

## 🔐 Security & Configuration

### **Environment Management**
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Env Vars** | python-dotenv | 1.0.0 | Load environment variables from .env |
| **Config File** | .env | Runtime configuration |

### **Key Configurations**
```
DATABASE:
  POSTGRES_HOST=postgres-mlops
  POSTGRES_PORT=5432
  MLOPS_DB_NAME=mlops
  POSTGRES_USER=mlops
  POSTGRES_PASSWORD=mlops

MONITORING:
  MONITORING_INTERVAL=300          (5 minutes)
  MONITORING_LOOKBACK=24           (24 hours)

RETRAINING GATES:
  MIN_F1_IMPROVEMENT_PCT=2.0       (Require 2% improvement)
  MAX_BRIER_DEGRADATION=0.01       (Allow 1% calibration loss)
  MIN_SAMPLES_FOR_DECISION=200     (Statistical validity)
  MIN_COVERAGE_PCT=30.0            (Label coverage)
  PROMOTION_COOLDOWN_DAYS=7        (Days between promotions)
```

---

## 📈 Observability & Monitoring

### **Dashboards & UIs**
| Dashboard | URL | Purpose |
|-----------|-----|---------|
| **MLflow UI** | http://localhost:5000 | Experiment tracking + model registry |
| **API Docs** | http://localhost:8000/docs | FastAPI Swagger documentation |
| **Airflow UI** | http://localhost:8080 | DAG scheduling and monitoring |
| **PgAdmin** | http://localhost:5050 | PostgreSQL database management |

### **Monitoring & Alerts**
| Component | Type | Purpose |
|-----------|------|---------|
| **Drift Detection** | Evidently AI | Statistical anomaly detection |
| **Proxy Metrics** | Custom Analytics | Label-free model performance monitoring |
| **Drift Reports** | HTML/Plotly | Interactive visualization of drift |
| **Retraining Logs** | Airflow Logs | DAG execution history and debugging |

---

## 🎯 Key Metrics & Evaluation

### **Model Performance Metrics**
| Metric | Description |
|--------|-------------|
| **F1 Score** | Primary performance metric |
| **Precision** | True positives / predicted positives |
| **Recall** | True positives / actual positives |
| **Brier Score** | Probability calibration measure |
| **AUC-ROC** | Binary classification performance |

### **Drift Detection Metrics**
| Metric | Description |
|--------|-------------|
| **Feature Drift Ratio** | % of features with detected drift |
| **Dataset Drift Detected** | Boolean: is overall dataset drift present? |
| **Num Drifted Features** | Count of features with drift |
| **Proxy Metrics** | Positive rate, probability mean/std, entropy |

### **System Metrics**
| Metric | Description |
|--------|-------------|
| **Label Coverage** | % of predictions with ground truth labels |
| **Samples for Evaluation** | Count of labeled predictions available |
| **Promotion Cooldown** | Days since last model promotion |
| **Training Success Rate** | % of retraining attempts that succeed |

---

## 📦 Dependency Management

### **Python Dependencies** (see requirements.txt)
```
Total Packages: 30+
├─ Core ML: scikit-learn, pandas, numpy
├─ API: FastAPI, Uvicorn, Pydantic
├─ Monitoring: Evidently AI, Plotly
├─ Orchestration: Airflow
├─ Database: psycopg2, SQLAlchemy
├─ Testing: pytest, pytest-timeout
├─ Quality: Black, Flake8, MyPy
├─ Utilities: python-dotenv, joblib, requests
└─ Observability: OpenTelemetry
```

### **System Dependencies**
```
Docker: 20.10+
Docker Compose: 2.0+
PostgreSQL: 13+
Git: 2.30+
Python: 3.10+
```

---

## 🚀 Deployment Model

### **Development**
- Docker Compose (single-server)
- SQLite for quick testing
- Local file storage

### **Production-Ready**
- Kubernetes (recommended)
- PostgreSQL (separate instance)
- Cloud storage (S3/GCS)
- Kafka for streaming predictions
- Prometheus for monitoring

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Lines of Code** | 8000+ |
| **Test Coverage** | 87.5% |
| **Docker Services** | 10 |
| **Database Tables** | 6 |
| **API Endpoints** | 5+ |
| **Evaluation Gates** | 6 |
| **Python Packages** | 30+ |

---

## 🔗 Comprehensive Architecture Diagram

```
╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                           SELF-HEALING ML-OPS SYSTEM ARCHITECTURE                                       ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                          EXTERNAL LAYER                                                 │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                         │
│    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐       ┌───────────────┐       │
│    │   End User   │         │ Monitoring   │         │  Data         │       │   Data        │       │
│    │ Predictions  │         │  Dashboard   │         │  Scientists   │       │   Ops Team    │       │
│    └──────┬───────┘         └──────┬───────┘         └────────┬──────┘       └───────┬───────┘       │
│           │                        │                         │                        │              │
└───────────┼────────────────────────┼─────────────────────────┼────────────────────────┼──────────────┘
            │                        │                         │                        │
            ▼                        ▼                         ▼                        ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     API & SERVING LAYER                                             │
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI Server (Port 8000)                                                                 │   │
│  │  ├─ POST /predict          (Credit Risk Prediction)                                         │   │
│  │  ├─ GET /health            (Health Check)                                                   │   │
│  │  ├─ GET /model/info        (Model Metadata)                                                 │   │
│  │  └─ WebSocket /live        (Real-time Updates)                                              │   │
│  │                                                                                             │   │
│  │  Components: Pydantic Validation → Request Handling → Response Serialization                │   │
│  └────────────────────┬──────────────────────────────────────────────────────────────────────┘   │
│                       │                                                                        │
└───────────────────────┼────────────────────────────────────────────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │  Load Model from MLflow Registry     │
        │  (Production Version)                 │
        │  ├─ scikit-learn (Logistic Reg)      │
        │  ├─ Feature Preprocessing             │
        │  └─ Probability Output                │
        └──────────┬────────────────────────────┘
                   │
                   ▼
        ┌───────────────────────────────────────┐
        │  Generate Prediction                  │
        │  ├─ Probability Score (0-1)          │
        │  ├─ Feature Values (16 features)      │
        │  ├─ Timestamp                         │
        │  └─ Request ID                        │
        └──────────┬────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         ▼                    ▼
    ┌──────────────────┐  ┌──────────────────┐
    │ Prediction        │  │ Response to User │
    │ Logger            │  │                  │
    │ (Append-only)     │  │ JSON with        │
    └────────┬──────────┘  │ prediction score │
             │             └──────────────────┘
             ▼

┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   LOGGING & STORAGE LAYER                                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  ┌──────────────────────────────────┐         ┌──────────────────────────────────┐               │
│  │  PostgreSQL (Port 5433)          │         │  CSV File Storage                │               │
│  │  MLOPS Database                  │         │  (Audit Trail)                   │               │
│  │                                  │         │                                  │               │
│  │  ┌─ prediction_logs              │         │  ├─ predictions.csv              │               │
│  │  │  └─ All predictions with       │         │  │  (append-only log)           │               │
│  │  │    features, scores, metadata  │         │  │                              │               │
│  │  │                                │         │  ├─ labels.csv                  │               │
│  │  ├─ label_store                  │         │  │  (ground truth feedback)      │               │
│  │  │  └─ Ground truth labels        │         │  │                              │               │
│  │  │    (async from users/labels)   │         │  └─ reference_data.csv          │               │
│  │  │                                │         │     (immutable baseline)        │               │
│  │  ├─ monitoring_metrics           │         └──────────────────────────────────┘               │
│  │  │  └─ Drift results & proxy      │                                                          │
│  │  │    metrics from scheduler      │         ┌──────────────────────────────────┐               │
│  │  │                                │         │  JSON File Storage               │               │
│  │  ├─ retraining_decisions         │         │  (Analysis & Reports)            │               │
│  │  │  └─ Trigger reason, gate       │         │                                  │               │
│  │  │    results, promotion action   │         │  ├─ monitoring_results/         │               │
│  │  │                                │         │  │  └─ monitoring_*.json         │               │
│  │  └─ model_metadata               │         │  │     (drift & metrics)         │               │
│  │     └─ Version info & deployment  │         │  │                              │               │
│  │       status                      │         │  ├─ drift_reports/              │               │
│  └──────────────────────────────────┘         │  │  └─ drift_*.html              │               │
│                                                │  │     (interactive visualization)│               │
│                                                │  │                              │               │
│                                                │  └─ decisions/                  │               │
│                                                │     └─ decision_*.json          │               │
│                                                │        (retraining decisions)   │               │
│                                                └──────────────────────────────────┘               │
│                                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                    │
                        ┌───────────────────────────┴───────────────────────────┐
                        │                                                       │
                        ▼                                                       ▼
        ┌─────────────────────────────────────┐           ┌────────────────────────────────────┐
        │ Data Available in Storage           │           │ Async Ground Truth Labels         │
        │ (Every prediction logged)           │           │ (From users/label service)        │
        │ • Features                          │           │ • Label ID matches Prediction ID  │
        │ • Scores                            │           │ • May arrive hours/days later     │
        │ • Metadata                          │           │ • Coverage ~30-40% typical        │
        └──────────────┬──────────────────────┘           └────────────────┬───────────────────┘
                       │                                                   │
        ┌──────────────┴──────────────────────────────────────────────────┴─────────────────┐
        │                                                                                    │
        ▼                                                                                    ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            MONITORING SCHEDULER LAYER (Every 5 Minutes)                             │
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  ┌─ Task Scheduler (SimpleScheduler)                                                              │
│  │  Frequency: 300 seconds (5 minutes)                                                             │
│  │  Location: monitoring-scheduler container                                                       │
│  │                                                                                                  │
│  └─ Steps:                                                                                        │
│     1. Load predictions from last 24 hours                                                        │
│     2. Load reference data (immutable baseline)                                                    │
│     3. Calculate proxy metrics:                                                                    │
│        └─ positive_rate (% positive class)                                                         │
│        └─ probability_mean (avg prediction score)                                                  │
│        └─ probability_std (variance in scores)                                                     │
│        └─ entropy (prediction uncertainty)                                                         │
│     4. Perform statistical drift detection:                                                        │
│        └─ Column drift check (each feature)                                                        │
│        └─ Target drift check (prediction distribution)                                             │
│     5. Compile drift analysis report                                                               │
│     6. Write results to PostgreSQL monitoring_metrics table                                         │
│     7. Generate interactive drift report (HTML + Plotly)                                            │
│                                                                                                      │
│  Technology: Evidently AI (drift detection engine)                                                 │
│              Plotly (visualization)                                                                 │
│              PostgreSQL (results storage)                                                           │
│                                                                                                      │
└──────────────────────┬──────────────────────────────────────────────────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
    ┌──────────────────┐     ┌──────────────────────┐
    │  Monitoring      │     │ Drift Detection      │
    │  Results         │     │ Results              │
    │  (PostgreSQL)    │     │                      │
    │                  │     │ ├─ feature_drift_    │
    │  ├─ positive_    │     │ │  ratio (%)         │
    │  │ rate          │     │ │                    │
    │  ├─ prob_mean    │     │ ├─ dataset_drift_    │
    │  ├─ prob_std     │     │ │  detected (bool)   │
    │  ├─ entropy      │     │ │                    │
    │  └─ timestamp    │     │ ├─ drifted_features  │
    │                  │     │ │  list              │
    └──────────────────┘     └────────┬─────────────┘
                                      │
                                      ▼
                            ┌──────────────────────┐
                            │ Drift Alert Decision │
                            │                      │
                            │ If drift_ratio > 20%:│
                            │ └─ Flag for manual   │
                            │   inspection         │
                            │ If dataset_drift:    │
                            │ └─ Log alert         │
                            │                      │
                            │ If drifted_features  │
                            │ > 5: Signal warning  │
                            └──────────────────────┘
                                      │
        ┌─────────────────────────────┴─────────────────────────────┐
        │                                                            │
        ▼                                                            ▼
    [Dashboard]                                         [Airflow DAG Ready]
    (Drift Alerts)                                      (If drift severe)

┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER: AIRFLOW RETRAINING DAG                                      │
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  Trigger Conditions:                                                                               │
│  • Weekly schedule (e.g., Monday 2 AM)                                                             │
│  • Manual trigger (data scientist decision)                                                        │
│  • Drift-triggered (if monitoring detects severe drift)                                             │
│                                                                                                      │
│  DAG: retraining_pipeline                                                                          │
│  Orchestrator: Apache Airflow 2.7.3                                                                │
│  Database: PostgreSQL (Airflow metadata)                                                           │
│  Logs: Airflow logs (viewable in UI)                                                               │
│                                                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  TASK 1: Check Retraining Conditions                                                         │ │
│  │  └─ Check days since last promotion (cooldown)                                               │ │
│  │  └─ Check available labeled samples                                                          │ │
│  │  └─ If conditions not met → SKIP remaining tasks                                             │ │
│  │  └─ If conditions met → PROCEED                                                              │ │
│  └────────────────┬────────────────────────────────────────────────────────────────────────────┘ │
│                   │ (Labeled data available & cooldown passed)                                   │
│                   ▼                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  TASK 2: Prepare Training Data                                                              │ │
│  │  ├─ Query labeled predictions from PostgreSQL                                                │ │
│  │  ├─ Apply temporal validation split                                                          │ │
│  │  ├─ Feature engineering & preprocessing                                                      │ │
│  │  └─ Save training/test datasets                                                              │ │
│  └────────────────┬────────────────────────────────────────────────────────────────────────────┘ │
│                   │                                                                              │
│                   ▼                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  TASK 3: Train Shadow Model                                                                  │ │
│  │  ├─ Load training data                                                                       │ │
│  │  ├─ Train new Logistic Regression model                                                      │ │
│  │  │  └─ Hyperparameters tuned via GridSearchCV                                                │ │
│  │  ├─ Evaluate on test set                                                                     │ │
│  │  │  └─ Calculate: F1, Precision, Recall, AUC-ROC, Brier Score                               │ │
│  │  ├─ Log experiment to MLflow                                                                 │ │
│  │  │  └─ Run ID, metrics, parameters, model artifact                                           │ │
│  │  └─ Model saved as .pkl in MLflow artifacts                                                  │ │
│  └────────────────┬────────────────────────────────────────────────────────────────────────────┘ │
│                   │ (Shadow model trained & logged)                                             │
│                   ▼                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  TASK 4: Evaluation Gate (6 Criteria)                                                        │ │
│  │  ├─ Gate 1: F1 Improvement              (min_improvement >= 2.0%)                            │ │
│  │ │  └─ Compare: new_f1 vs production_f1                                                      │ │
│  │  │                                                                                           │ │
│  │  ├─ Gate 2: Brier Score (Calibration)  (max_degradation <= 0.01)                            │ │
│  │  │  └─ Probability calibration check                                                        │ │
│  │  │                                                                                           │ │
│  │  ├─ Gate 3: Min Samples for Decision   (min_samples >= 200)                                 │ │
│  │  │  └─ Ensure statistical validity                                                          │ │
│  │  │                                                                                           │ │
│  │  ├─ Gate 4: Label Coverage             (coverage >= 30%)                                    │ │
│  │  │  └─ % of predictions with labels    (e.g., 200/667 = 30%)                               │ │
│  │  │                                                                                           │ │
│  │  ├─ Gate 5: Recall Threshold           (recall >= min_recall)                               │ │
│  │  │  └─ Ensure minority class detection                                                      │ │
│  │  │                                                                                           │ │
│  │  └─ Gate 6: AUC-ROC Threshold          (auc >= 0.72)                                        │ │
│  │     └─ Overall discrimination ability                                                        │ │
│  │                                                                                               │ │
│  │  Result: ALL gates must pass → PROCEED | ANY gate fails → STOP                               │ │
│  └────────────────┬──────────────────────────────┬──────────────────────────────────────────────┘ │
│                   │ (ALL gates passed)           │ (ANY gate failed)                              │
│                   ▼                              ▼                                               │
│         ┌──────────────────┐          ┌──────────────────────────────┐                          │
│         │ Log Decision     │          │ Reject Model                 │                          │
│         │ APPROVED         │          │ Log Decision: REJECTED       │                          │
│         │ (in DB)          │          │ Reason: Failed gate X        │                          │
│         │                  │          │ Archive run in MLflow        │                          │
│         └────────┬─────────┘          │ Monitor manually             │                          │
│                  │                    └──────────────────────────────┘                          │
│         ┌────────┴────────┐                      │                                              │
│         │                 │                      │                                              │
│         ▼                 ▼                      ▼                                              │
│  ┌──────────────────┐ (If gates fail)  [End Workflow]                                         │
│  │ TASK 5:          │ └─ Alert DS team                                                        │
│  │ Promote Model    │                                                                         │
│  │                  │                                                                         │
│  │ 1. Register as   │                                                                         │
│  │    "Staging"     │                                                                         │
│  │ 2. Run final     │                                                                         │
│  │    validation    │                                                                         │
│  │    tests         │                                                                         │
│  │ 3. Promote to    │                                                                         │
│  │    "Production"  │                                                                         │
│  │ 4. Archive old   │                                                                         │
│  │    model         │                                                                         │
│  │ 5. Update        │                                                                         │
│  │    metadata      │                                                                         │
│  └────────┬─────────┘                                                                        │
│           │                                                                                   │
└───────────┼──────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   MODEL REGISTRY LAYER                                             │
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  MLflow Model Registry (Port 5000)                                                                 │
│  ├─ Model Name: "credit-risk-model"                                                               │
│  │                                                                                                  │
│  ├─ Versions (History):                                                                            │
│  │  ├─ Version 1 → Stage: Archived (old)                                                          │
│  │  ├─ Version 2 → Stage: Archived (older)                                                        │
│  │  ├─ Version 3 → Stage: PRODUCTION (current serving)                                            │
│  │  └─ Version 4 → Stage: Staging (latest trained, awaiting promotion)                            │
│  │                                                                                                  │
│  ├─ Artifacts per Version:                                                                        │
│  │  └─ models.pkl               (serialized scikit-learn model)                                   │
│  │  └─ metrics.json             (performance metrics)                                             │
│  │  └─ params.json              (hyperparameters)                                                 │
│  │  └─ requirements.txt          (dependencies)                                                    │
│  │  └─ metadata.json            (version info)                                                    │
│  │                                                                                                  │
│  ├─ Experiment Tracking:                                                                          │
│  │  └─ Each retraining → New MLflow Run                                                           │
│  │  └─ Run logs: metrics, parameters, artifacts                                                   │
│  │  └─ Versioned artifacts storage: mlflow/artifacts/{run_id}/                                     │
│  │                                                                                                  │
│  └─ Storage Backend:                                                                              │
│     ├─ Metadata: SQLite / PostgreSQL (Airflow metadata DB)                                        │
│     └─ Artifacts: File system (mlflow/artifacts/) or S3 (cloud)                                   │
│                                                                                                      │
└──────────────┬───────────────────────────────────────────────────────────────────────────────────┘
               │
               │ Production Version (v3)
               │ loaded by FastAPI
               │
               ▼
            [Back to API layer]
            Ready for next predictions

┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              DOCKER CONTAINERIZATION LAYER                                         │
├──────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│  Network: mlops-network (bridge network)                                                           │
│                                                                                                      │
│  Services (10 containers):                                                                         │
│                                                                                                      │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐         │
│  │ postgres                 │  │ postgres-mlops           │  │ pgadmin                  │         │
│  │ (Airflow metadata DB)    │  │ (MLOps application DB)   │  │ (Postgres UI)            │         │
│  │ Port: 5432              │  │ Port: 5433               │  │ Port: 5050               │         │
│  └──────────────────────────┘  └──────────────────────────┘  └──────────────────────────┘         │
│                                                                                                      │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐         │
│  │ mlflow                   │  │ airflow-webserver        │  │ airflow-scheduler        │         │
│  │ (Model registry & track) │  │ (DAG UI)                 │  │ (DAG execution engine)   │         │
│  │ Port: 5000              │  │ Port: 8080               │  │ Port: Internal           │         │
│  └──────────────────────────┘  └──────────────────────────┘  └──────────────────────────┘         │
│                                                                                                      │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐         │
│  │ api                      │  │ monitoring-scheduler     │  │ trainer                  │         │
│  │ (FastAPI serving)        │  │ (5-min drift detection)  │  │ (Retraining job)         │         │
│  │ Port: 8000              │  │ Port: Internal           │  │ Port: Internal           │         │
│  └──────────────────────────┘  └──────────────────────────┘  └──────────────────────────┘         │
│                                                                                                      │
│  Shared Volumes:                                                                                    │
│  • postgres-db-volume       (Airflow DB persistence)                                               │
│  • postgres-mlops-volume    (MLOps DB persistence)                                                 │
│  • ./mlflow                 (MLflow artifacts)                                                      │
│  • ./monitoring             (Drift reports & metrics)                                               │
│  • ./data                   (Training data)                                                         │
│                                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘

╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                    DATA FLOW SUMMARY                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

1. USER PREDICTION REQUEST
   User → FastAPI /predict → Load Model from MLflow → Generate Score → Response

2. PREDICTION LOGGING (Immediate)
   Prediction → PostgreSQL prediction_logs + CSV predictions.csv → Audit Trail

3. LABEL FEEDBACK (Async, hours/days later)
   User Label → PostgreSQL label_store + CSV labels.csv → Ground Truth

4. MONITORING (Every 5 min)
   Predictions + Reference → Evidently AI → Drift Detection → PostgreSQL monitoring_metrics

5. RETRAINING (Weekly or Drift-Triggered)
   Labeled Data → Airflow DAG → Shadow Train → 6-Gate Evaluation → Promotion → MLflow Registry

6. SERVING (Continuous)
   FastAPI loads new Production version from MLflow → Serves next prediction

╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                     KEY INTERACTIONS                                                   ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

• FastAPI ↔ MLflow: Load/update models
• FastAPI ↔ PostgreSQL: Log predictions
• Monitoring ↔ PostgreSQL: Read predictions, write metrics
• Monitoring ↔ CSV: Audit trail access
• Airflow ↔ PostgreSQL: Store DAG metadata, read for training
• Airflow ↔ MLflow: Log experiments, promote models
• Drift Detection ↔ Evidently AI: Statistical analysis
• Retraining Gate ↔ PostgreSQL: Read evaluation results

╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                   RESILIENCE & FAILOVER                                                ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

✓ Dual storage (PostgreSQL + CSV) → If one fails, audit trail preserved
✓ MLflow artifact versioning → Can rollback to previous model
✓ Evaluation gates → Prevents bad models from going to production
✓ Monitoring → Detects performance degradation quickly
✓ Immutable reference data → Baseline never corrupted
✓ Async label feedback → Non-blocking prediction service
```

---

## Architecture Highlights

### **Real-Time Prediction Path** (~100ms)
```
FastAPI → Load Model → Predict → Log → Response
```

### **Monitoring Path** (Every 5 minutes)
```
PostgreSQL → Load Predictions → Reference Data → Drift Detection → Results
```

### **Retraining Path** (Weekly or Drift-Triggered)
```
Labeled Data → Airflow → Train → 6 Gates → MLflow Registry → Serving
```

### **Key Design Principles**
1. **Immutable Reference Data** - Never changes, used for drift baseline
2. **Async Labels** - Don't block predictions while waiting for feedback
3. **Multi-Gate Evaluation** - 6 criteria prevent bad models from shipping
4. **Dual Storage** - PostgreSQL for queries, CSV for audit trail
5. **Containerized Services** - Each component isolated and independently deployable
6. **MLflow Registry** - Single source of truth for model versions

---

## 📚 Documentation
- **README.md** - Quick start and overview
- **architecture.md** - Detailed system design
- **evaluation_gates.md** - Retraining criteria
- **TECHSTACK.md** - This file
- **runbook.md** - Operations guide
- **api.md** - API reference

---

## ✅ Strengths & Tradeoffs

### **Strengths**
✅ Hybrid storage (PostgreSQL + Files) for reliability and auditability
✅ Dual orchestration (Monitoring scheduler + Airflow) for flexibility
✅ 6-gate evaluation system for safe promotions
✅ Comprehensive testing and CI/CD
✅ Production-ready containerization

### **Current Tradeoffs**
⚠️ Hybrid storage requires sync logic (acknowledged drawback)
⚠️ Single-server deployment (not horizontally scalable)
⚠️ CSV files limit performance for high-volume scenarios

### **Future Improvements**
🚀 Kafka for streaming predictions
🚀 Kubernetes for orchestration
🚀 S3/GCS for artifact storage
🚀 Feature store integration
🚀 Model explainability (SHAP/LIME)

---

**Last Updated:** January 29, 2026
**Version:** 1.0
