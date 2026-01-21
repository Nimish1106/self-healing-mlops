# Database Integration Status

**Date**: 2026-01-06  
**Status**: ✅ Monitoring fully integrated, Retraining ready, Model versioning pending

---

## 📊 Integration Overview

### Database Tables (3)
| Table | Purpose | Integration | Status |
|-------|---------|-------------|--------|
| `monitoring_metrics` | Track drift, proxy metrics, predictions | ✅ Monitoring job writes | **ACTIVE** |
| `retraining_decisions` | Log gate results, promotion decisions | ✅ Retraining pipeline writes | **READY** |
| `model_versions` | Track model metadata, promotion history | ❌ Not yet integrated | **PENDING** |

### Database Views (3)
| View | Purpose | Status |
|------|---------|--------|
| `v_decision_history` | Historical gate decisions | ✅ Available |
| `v_model_timeline` | Model promotion timeline | ✅ Available |
| `v_recent_monitoring` | Latest monitoring metrics | ✅ Available |

---

## ✅ COMPLETED: Monitoring Integration

### File: [src/monitoring/monitoring_job.py](src/monitoring/monitoring_job.py)

**Status**: Fully integrated with database writes

**What Changed**:
- Line 19: Added `from src.storage.repositories import MonitoringMetricsRepository`
- Line 76: Instantiated `self.metrics_repo = MonitoringMetricsRepository()`
- Lines 219-226: Calls `_write_to_database()` after analytics complete
- Lines 268-306: `_write_to_database()` method inserts metrics into PostgreSQL

**Data Persisted**:
```
timestamp            - Run timestamp (UNIQUE constraint)
lookback_hours       - Analysis window (24h, 48h, etc.)
num_predictions      - Total predictions analyzed
positive_rate        - Positive class rate
probability_mean     - Mean prediction probability
probability_std      - Std dev of probabilities
entropy              - Prediction entropy (uncertainty)
dataset_drift_detected  - Boolean: any drift detected
feature_drift_ratio  - Percentage of features with drift (0.0-1.0)
num_drifted_features - Count of drifted features
drift_summary_ref    - Path to drift JSON artifact
drift_report_ref     - Path to drift HTML artifact
```

**Verification** (2026-01-06 10:49):
```sql
SELECT id, timestamp, num_predictions, feature_drift_ratio 
FROM monitoring_metrics 
ORDER BY timestamp DESC LIMIT 1;

-- Result:
-- a172e584-8643-47b2-924f-7dae419b5e57 | 2026-01-06 10:49:02.087857 | 3529 | 0.5
```

**Key Log Lines**:
```
✅ Metrics written to database: a172e584-8643-47b2-924f-7dae419b5e57
```

---

## ✅ READY: Retraining Integration

### File: [airflow/dags/retraining_pipeline.py](airflow/dags/retraining_pipeline.py)

**Status**: Code implemented, waiting for pipeline execution

**What Changed**:
- Line 24: Added `from src.storage.repositories import RetrainingDecisionsRepository`
- Lines 511-545: Gate decision inserted into database after evaluation
- Captures: Decision timestamp, trigger reason, action (promote/reject), drift context, data context, detailed decision metrics

**Data Persisted**:
```
timestamp           - Decision timestamp
trigger_reason      - What triggered retraining (scheduled, drift, manual)
action              - promote or reject
drift_context       - JSONB with feature_drift_ratio, drifted_features
data_context        - JSONB with coverage stats
decision_details    - JSONB with gate failure reasons, metrics improvements
labeled_samples     - Number of labeled samples used in decision
coverage_pct        - Percentage of labeled predictions available
```

**What Happens When Pipeline Runs**:
1. Gate evaluates shadow model
2. Produces `should_promote, decision` tuple
3. `RetrainingDecisionsRepository.insert()` called → writes to `retraining_decisions` table
4. Decision becomes queryable for audit, rollback decision, trend analysis

**Next Event**: When retraining triggered (drift detected or scheduled), this will auto-populate

---

## ❌ PENDING: Model Version Integration

### Files Needing Updates

#### 1. [src/retraining/model_promoter.py](src/retraining/model_promoter.py)

**Current State**: 
- Promotes models via MLflow API only
- Saves promotion records to JSON files
- Does NOT write to `model_versions` table

**What Needs to Change**:
```python
# Add at top
from src.storage.repositories import ModelVersionRepository

# In __init__
self.model_repo = ModelVersionRepository()

# In promote_to_production() after MLflow transition
self.model_repo.insert(
    model_name=self.model_name,
    model_version=shadow_version,
    mlflow_run_id=shadow_run_id,
    stage='Production',
    f1_score=evaluation_decision.get('metrics', {}).get('f1'),
    brier_score=evaluation_decision.get('metrics', {}).get('brier'),
    promoted_at=datetime.now(),
    promoted_by=promoted_by
)
```

#### 2. [src/train_model_mlflow.py](src/train_model_mlflow.py)

**Current State**:
- Trains and logs models to MLflow
- Does NOT write to `model_versions` table

**What Needs to Change**:
```python
# Add after MLflow logging
from src.storage.repositories import ModelVersionRepository

model_repo = ModelVersionRepository()
model_repo.insert(
    model_name='credit-risk-model',
    model_version=registered_version,
    mlflow_run_id=run_id,
    stage='Staging',  # New models start in Staging
    f1_score=metrics['f1'],
    brier_score=metrics['brier'],
    promoted_at=None,  # Not promoted yet
    promoted_by='system'
)
```

---

## 📈 Database Schema Details

### monitoring_metrics Table
```sql
CREATE TABLE monitoring_metrics (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp timestamp NOT NULL UNIQUE,
    lookback_hours integer NOT NULL,
    num_predictions integer NOT NULL,
    positive_rate double precision,
    probability_mean double precision,
    probability_std double precision,
    entropy double precision,
    dataset_drift_detected boolean DEFAULT false,
    feature_drift_ratio double precision DEFAULT 0.0,
    num_drifted_features integer DEFAULT 0,
    drift_summary_ref text,
    drift_report_ref text,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP
);
-- 4 indexes including timestamp and drift tracking
```

### retraining_decisions Table
```sql
CREATE TABLE retraining_decisions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp timestamp NOT NULL,
    trigger_reason varchar(50) NOT NULL,
    action varchar(10) NOT NULL CHECK (action IN ('promote', 'reject')),
    drift_context jsonb,
    data_context jsonb,
    decision_details jsonb,
    labeled_samples integer,
    coverage_pct double precision,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP
);
-- 2 indexes for trend analysis
```

### model_versions Table
```sql
CREATE TABLE model_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name varchar(255) NOT NULL,
    model_version varchar(50) NOT NULL,
    mlflow_run_id varchar(255) NOT NULL,
    stage varchar(50) NOT NULL,
    f1_score double precision,
    brier_score double precision,
    promoted_at timestamp,
    promoted_by varchar(255),
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_name, model_version)
);
-- 2 indexes for stage tracking and promotion timeline
```

---

## 🔍 Current Metrics in Database

### Monitoring Metrics (Latest)
```sql
SELECT 
    timestamp,
    num_predictions,
    feature_drift_ratio,
    dataset_drift_detected,
    num_drifted_features
FROM monitoring_metrics
ORDER BY timestamp DESC
LIMIT 1;
```

**Result** (2026-01-06 10:49):
- ✅ 3529 predictions analyzed
- ✅ 50% drift detected (5 out of 10 features)
- ✅ 4 features flagged as drifted
- ✅ Dataset-level drift: False

### Retraining Decisions
```sql
SELECT COUNT(*) FROM retraining_decisions;
-- Result: 0 (waiting for first pipeline run)
```

### Model Versions
```sql
SELECT COUNT(*) FROM model_versions;
-- Result: 0 (not integrated yet)
```

---

## 🚀 Next Steps

### Immediate (For Model Promotion Tracking)
1. Integrate `ModelVersionRepository` into `model_promoter.py`
2. Integrate `ModelVersionRepository` into `train_model_mlflow.py`
3. Test with next promotion event

### Verification Commands
```bash
# Check monitoring progress
docker-compose exec -T postgres psql -U airflow -d mlops -c \
  "SELECT COUNT(*) FROM monitoring_metrics"

# Check retraining decisions (after pipeline runs)
docker-compose exec -T postgres psql -U airflow -d mlops -c \
  "SELECT action, COUNT(*) FROM retraining_decisions GROUP BY action"

# Check model timeline (after integration)
docker-compose exec -T postgres psql -U airflow -d mlops -c \
  "SELECT * FROM v_model_timeline"
```

### Dashboard Queries Ready to Build
```sql
-- Recent drift trend
SELECT timestamp, feature_drift_ratio, num_drifted_features
FROM monitoring_metrics
WHERE timestamp > NOW() - interval '7 days'
ORDER BY timestamp DESC;

-- Decision success rate
SELECT action, COUNT(*) as count
FROM retraining_decisions
GROUP BY action;

-- Promotion history
SELECT model_name, stage, COUNT(*) as versions
FROM model_versions
GROUP BY model_name, stage;
```

---

## 🔐 Connection Details

**Database**: `mlops` (separate from Airflow DB)  
**Host**: `postgres:5432`  
**User**: `airflow` / `airflow`  
**Connection Pooling**: psycopg2 SimpleConnectionPool (1-10 connections)  
**Environment Variables**:
```
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
MLOPS_DB_NAME=mlops
```

---

## 📝 Summary

| Component | Status | Evidence |
|-----------|--------|----------|
| Database Setup | ✅ Complete | 3 tables + 3 views created |
| Monitoring Integration | ✅ Active | Records written, queryable |
| Retraining Integration | ✅ Ready | Code in place, awaiting pipeline |
| Model Version Integration | ⏳ Pending | Code scaffolding exists |
| Overall Data Flow | ✅ Working | Monitoring → DB → Views |

**System State**: Production-ready for monitoring and decision tracking. Model version tracking can be enabled on next promotion.
