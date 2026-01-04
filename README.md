# Self-Healing MLOps: Credit Risk Model with Continuous Monitoring & Retraining

A **production-grade ML system** that autonomously detects model degradation, evaluates retraining candidates, and makes promotion decisions—all while maintaining data integrity and fairness constraints.

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SELF-HEALING MLOPS PIPELINE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Phase 1: Training         │  Phase 2: Production Serving        │
│  • MLflow tracking         │  • FastAPI credit risk API          │
│  • Model versioning        │  • Prediction logging               │
│  • Hyperparameter tuning   │  • Label collection                 │
│                            │                                     │
├────────────────────────────┼──────────────────────────────────────┤
│                            │                                      │
│  Phase 3: Monitoring       │  Phase 4: Decision & Retraining     │
│  • Drift detection         │  • Evaluation gates                  │
│  • Proxy metrics           │  • Shadow model training            │
│  • Evidently reports       │  • Model promotion logic            │
│                            │  • Cooldown enforcement             │
│                            │                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 🏗️ System Components

### **Phase 1: Model Training** (`src/train_model_mlflow.py`)
- Baseline model development using scikit-learn
- Hyperparameter tuning with GridSearchCV
- MLflow experiment tracking (metrics, params, artifacts)
- Model versioning with production stage tags

### **Phase 2: Production API** (`src/api_mlflow.py`)
- FastAPI service serving production model
- Real-time credit risk predictions (0-1 probability)
- Prediction logging with timestamps and features
- Inference telemetry for downstream monitoring

### **Phase 3: Drift Monitoring** (`src/analytics/drift_detection.py`)
**Evidently v0.4.15 statistical drift detection**
- **DatasetDriftMetric**: Overall distribution change detection
- **ColumnDriftMetric**: Feature-level drift using Wasserstein distance
- Reference baseline (frozen 30K samples from training set)
- 24-hour lookback window for current data
- HTML drift reports + JSON summaries with complete feature details

**Drift Summary Structure** (example):
```json
{
  "timestamp": "2026-01-04T09:33:59.180318",
  "dataset_drift_detected": true,
  "drift_share": 0.5,
  "num_drifted_features": 6,
  "num_features_total": 10,
  "num_features_evaluated": 10,
  "excluded_features": [],
  "features": [
    {
      "feature": "MonthlyIncome",
      "drift_detected": true,
      "stat_test": "Wasserstein distance (normed)",
      "drift_score": 0.371,
      "threshold": 0.1
    }
  ]
}
```

### **Phase 4: Evaluation Gate & Promotion** (`src/retraining/evaluation_gate.py`)
**Multi-criteria gate ensuring only safe models are promoted:**

| Gate # | Criterion | Threshold | Purpose |
|--------|-----------|-----------|---------|
| 1 | Sufficient samples | ≥200 | Statistical power |
| 2 | Label coverage | ≥30% | Evaluation validity |
| 3 | Promotion cooldown | 7 days | Deployment stability |
| 4 | F1 improvement | ≥2% | Business value |
| 5 | Calibration maintained | Brier ≤+0.01 | Probability quality |
| 6 | No segment regression | F1 drop ≤5% | Fairness & safety |

**Decision Logic**: ALL gates must pass → Model promoted to production

## 📊 Data Flow

### Monitoring Pipeline (5-minute intervals)
```
Production Model
    ↓
Generate Predictions → Log to CSV
    ↓
Collect Last 24h Predictions (≈2000)
    ↓
Compute Proxy Metrics (coverage, patterns)
    ↓
Run Drift Detection (Evidently)
    ↓
Evaluate Against Reference Baseline
    ↓
[DRIFT DETECTED] → Signal retraining workflow
    ↓
Save HTML Report + JSON Summary
```

### Retraining Pipeline (triggered by drift)
```
[Drift Signal] → Trigger Retraining DAG (Airflow)
    ↓
Shadow Trainer: Train new model in parallel
    ↓
Wait for Labels (24-48h window)
    ↓
Evaluation Gate: Run 6-gate validation
    ↓
[ALL GATES PASS] → Promote to Production
[GATE FAILS] → Log rejection + wait
    ↓
Update Model Registry + Serve New Version
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10
- Git

### Setup & Run
```bash
# Clone repository
git clone https://github.com/Nimish1106/self-healing-mlops.git
cd self-healing-mlops

# Start all services (API, monitoring, MLflow, Airflow)
docker-compose up -d

# Bootstrap reference data (frozen baseline)
docker exec reference-bootstrap python scripts/bootstrap_reference.py

# Generate synthetic predictions (for testing)
docker exec credit-risk-api python scripts/generate_fake_predictions.py

# Monitor logs
docker logs monitoring-scheduler -f        # Drift detection
docker logs model-trainer -f               # Retraining
docker logs credit-risk-api -f            # API predictions
```

### Access Services
- **API Predictions**: `http://localhost:8000/predict`
- **MLflow Tracking**: `http://localhost:5000`
- **Airflow DAGs**: `http://localhost:8080`
- **Drift Reports**: `/app/monitoring/reports/drift_reports/`

## 📁 Directory Structure

```
self-healing-mlops/
├── src/
│   ├── api_mlflow.py                  # FastAPI service
│   ├── train_model_mlflow.py           # Training entrypoint
│   ├── analytics/
│   │   ├── drift_detection.py          # Phase 3: Evidently drift
│   │   ├── drift_signals.py            # Drift → retraining decision
│   │   ├── model_evaluator.py          # Shadow model evaluation
│   │   └── proxy_metrics.py            # Coverage, patterns
│   ├── monitoring/
│   │   └── monitoring_job.py           # 5-min scheduler
│   ├── retraining/
│   │   ├── evaluation_gate.py          # Phase 4: 6-gate validation
│   │   ├── shadow_trainer.py           # Parallel training
│   │   └── model_promoter.py           # Registry updates
│   ├── storage/
│   │   ├── prediction_logger.py        # CSV logging
│   │   └── label_store.py              # Label collection
│   └── utils/
│       ├── temporal_utils.py           # Time windows
│       └── dataset_fingerprint.py      # Data integrity
│
├── airflow/
│   └── dags/
│       └── retraining_pipeline.py      # Orchestration DAG
│
├── scripts/
│   ├── bootstrap_reference.py          # Freeze baseline
│   ├── generate_fake_predictions.py    # Testing data
│   ├── simulate_traffic.py             # Load simulation
│   └── run_retraining_workflow.py      # Manual trigger
│
├── monitoring/
│   ├── reference/                      # Frozen baseline
│   ├── predictions/                    # Production logs
│   ├── labels/                         # True outcomes
│   ├── metrics/                        # Evaluation results
│   └── reports/                        # Drift reports (HTML + JSON)
│
├── docker-compose.yml                 # Multi-service orchestration
├── Dockerfile                         # Main app image
└── Dockerfile.airflow                 # Airflow-specific image
```

## 🔍 Key Design Decisions

### 1. **Drift Detection: Distribution, Not Performance**
- Evidently detects **IF** distributions changed
- Does NOT evaluate **IF** model performance degraded
- Drift ≠ model failure (must wait for labels)
- Prevents reactive retraining on transient shifts

### 2. **Evaluation Gate: All-or-Nothing**
- Every gate acts as a circuit breaker
- Single failure → entire promotion blocked
- Rejection is **successful** system behavior
- No partial promotions or A/B testing

### 3. **Promotion Cooldown: Stability Over Optimization**
- 7-day minimum between promotions
- Prevents retraining storms
- Allows time to detect real-world issues
- Authority: EvaluationGate only (ModelPromoter trusted)

### 4. **Label Coverage: Practical Evaluation**
- Only ~30% of predictions get labels in 24h
- Minimum 30% coverage required for gate passage
- Balances waiting time vs. decision confidence
- Fail-closed if coverage_stats missing

### 5. **Segment Fairness: Explicit Checking**
- Feature → segment → performance tracked
- Detects if new model hurts minority groups
- ±5% F1 drop tolerance per segment
- Non-blocking for missing segments (insufficient data)

## 📈 Monitoring & Observability

### Drift Summary Files
Location: `/app/monitoring/reports/drift_reports/`
- `drift_summary_YYYYMMDD_HHMMSS.json` - Machine-readable summary
- `drift_report_YYYYMMDD_HHMMSS.html` - Visual Evidently report

### Decision Records
Location: `/app/monitoring/retraining/decisions/`
- `decision_*.json` - Gate pass/fail records
- Contains: timestamp, all gate results, final decision, reason

### Monitoring Results
Location: `/app/monitoring/metrics/monitoring_results/`
- `monitoring_YYYYMMDD_HHMMSS.json` - Aggregated metrics
- Proxy coverage, feature statistics, data freshness

## 🧪 Testing & Validation

### Generate Test Predictions
```bash
docker exec credit-risk-api python scripts/generate_fake_predictions.py
```

### Simulate Traffic
```bash
docker exec credit-risk-api python scripts/simulate_traffic.py --duration=3600
```

### Trigger Retraining Manually
```bash
docker exec model-trainer python scripts/run_retraining_workflow.py
```

## 📊 Implementation Metrics

| Component | Technology | Version |
|-----------|-----------|---------|
| Drift Detection | Evidently | 0.4.15 |
| ML Framework | scikit-learn | 1.3.2 |
| Feature Encoding | Categorical Encoding | 2.6.1 |
| Web Framework | FastAPI | 0.109.2 |
| Orchestration | Airflow | 2.7.3 |
| Model Registry | MLflow | 2.14.1 |
| Containerization | Docker | 27.x |
| Database | PostgreSQL | 15 |

## 🛡️ Safety & Correctness

- ✅ **Phase 3 Complete**: Full drift detection with feature-level details
- ✅ **Phase 4 Complete**: 6-gate evaluation with cooldown enforcement
- ✅ **Reference Immutability**: Frozen baseline never modified
- ✅ **Fail-Closed Gating**: Missing data → rejection, not bypass
- ✅ **Audit Trail**: All decisions logged with timestamps & rationale
- ✅ **Docker Isolation**: Clean layer builds, no cached code issues

## 🚦 Deployment Readiness

- [x] Code quality: Comprehensive logging & error handling
- [x] Testing: Docker builds without cache, services verified working
- [x] Documentation: README, inline comments, decision rationale
- [x] Configuration: All paths, thresholds, intervals configurable
- [x] Monitoring: Full observability with JSON logs & HTML reports
- [x] Git history: Clean commits with feature branches

## 📝 Recent Fixes (Phase 4)

### Critical Issue: Drift Summary Structure
**Problem**: JSON files missing feature-level details
- Old code: Only `drift_share`, `num_drifted_features`
- Expected: Complete feature array with drift scores, p-values

**Solution**: 
- Added `ColumnDriftMetric` for each feature
- Proper extraction from Evidently report structure
- Complete JSON with 10 required fields

**Validation**:
```bash
$ docker logs monitoring-scheduler 2>&1 | grep "Features array"
Drift summary | dataset_drift=True | drift_share=50.00% | drifted=6/10 evaluated (0 excluded)
Features array length: 10
✅ Drift summary structure is complete
```

## 🔗 Related Documentation

- **Phase 1**: Baseline model training & development
- **Phase 2**: Production API & prediction logging  
- **Phase 3**: Drift detection using Evidently
- **Phase 4**: Evaluation gates & model promotion (this phase)

## 📞 Support

For issues or questions:
1. Check Docker logs: `docker-compose logs [service-name]`
2. Review drift reports: `/monitoring/reports/drift_reports/`
3. Check decision records: `/monitoring/retraining/decisions/`
4. Verify monitoring metrics: `/monitoring/metrics/monitoring_results/`

---

**Status**: ✅ Phase 4 Complete & Ready for Production  
**Last Updated**: 2026-01-04  
**Branch**: `phase-4-mlops`
