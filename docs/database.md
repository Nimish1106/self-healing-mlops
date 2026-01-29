
# Database Documentation

**PostgreSQL schema and core operations for the Self-Healing MLOps system**

---

## Overview

**Database:** PostgreSQL 13
**Container:** `postgres-mlops`
**Database Name:** `mlops`
**User:** `mlops`
**Port:** `5432` (Docker) / `5433` (Host)

⚠️ Default credentials are for development only.

### Connection Strings

```text
postgresql://mlops:mlops@postgres-mlops:5432/mlops
postgresql://mlops:mlops@localhost:5433/mlops
```

---

## Schema

### `prediction_logs`

Stores all online predictions and features.

```sql
CREATE TABLE prediction_logs (
    id SERIAL PRIMARY KEY,
    prediction_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    model_version VARCHAR(50),
    model_stage VARCHAR(20),

    prediction INTEGER CHECK (prediction IN (0,1)),
    probability FLOAT CHECK (probability BETWEEN 0 AND 1),

    age INTEGER,
    debt_ratio FLOAT,
    monthly_income FLOAT,
    number_dependents INTEGER,

    request_source VARCHAR(100),
    response_time_ms INTEGER
);

CREATE INDEX idx_prediction_created_at ON prediction_logs(created_at);
CREATE INDEX idx_prediction_model_version ON prediction_logs(model_version);
```

---

### `label_store`

Delayed ground-truth labels for feedback learning.

```sql
CREATE TABLE label_store (
    id SERIAL PRIMARY KEY,
    prediction_id VARCHAR(255) UNIQUE
        REFERENCES prediction_logs(prediction_id),
    true_label INTEGER CHECK (true_label IN (0,1)),
    label_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    label_source VARCHAR(100),
    days_delayed INTEGER
);

CREATE INDEX idx_label_timestamp ON label_store(label_timestamp);
```

---

### `model_metadata`

Tracks model lifecycle and performance.

```sql
CREATE TABLE model_metadata (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) UNIQUE NOT NULL,
    model_stage VARCHAR(20),
    model_type VARCHAR(50),

    f1_score FLOAT,
    precision_score FLOAT,
    recall_score FLOAT,
    roc_auc FLOAT,
    brier_score FLOAT,

    trained_at TIMESTAMP,
    deployed_at TIMESTAMP,
    mlflow_run_id VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_stage ON model_metadata(model_stage);
```

---

### `monitoring_alerts`

Drift and performance alerts.

```sql
CREATE TABLE monitoring_alerts (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alert_type VARCHAR(50),
    severity VARCHAR(20),

    drift_share FLOAT,
    drifted_features TEXT[],
    message TEXT,
    metrics JSONB
);

CREATE INDEX idx_alert_created_at ON monitoring_alerts(created_at);
```

---

### `retraining_metrics`

Shadow-model evaluation and promotion decisions.

```sql
CREATE TABLE retraining_metrics (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    shadow_model_version VARCHAR(50),
    production_model_version VARCHAR(50),
    gate_passed BOOLEAN,
    promoted BOOLEAN,

    shadow_f1_score FLOAT,
    production_f1_score FLOAT,
    mlflow_run_id VARCHAR(255)
);

CREATE INDEX idx_retraining_promoted ON retraining_metrics(promoted);
```

---

## Common Queries

### Prediction Volume (Last 24h)

```sql
SELECT COUNT(*)
FROM prediction_logs
WHERE created_at > NOW() - INTERVAL '24 hours';
```

### Label Coverage

```sql
SELECT
  COUNT(ls.prediction_id)::float / COUNT(pl.prediction_id) AS coverage
FROM prediction_logs pl
LEFT JOIN label_store ls USING (prediction_id);
```

### Model Accuracy (With Labels)

```sql
SELECT
  model_version,
  AVG(pl.prediction = ls.true_label)::float AS accuracy
FROM prediction_logs pl
JOIN label_store ls USING (prediction_id)
GROUP BY model_version;
```

### Recent Drift Alerts

```sql
SELECT created_at, severity, drift_share
FROM monitoring_alerts
WHERE alert_type = 'drift'
ORDER BY created_at DESC
LIMIT 10;
```

---

## Maintenance

### Routine Maintenance

```sql
VACUUM ANALYZE prediction_logs;
VACUUM ANALYZE label_store;
VACUUM ANALYZE model_metadata;
```

---

## Backup & Recovery

### Full Backup

```bash
docker exec postgres-mlops pg_dump -U mlops mlops > mlops_backup.sql
```

### Restore

```bash
cat mlops_backup.sql | docker exec -i postgres-mlops psql -U mlops -d mlops
```

---

## Performance Notes

* Indexed on `created_at`, `model_version`, and `prediction_id`
* JSONB used only where schema flexibility is required
* Batch inserts recommended for high-throughput logging

---

## Security Notes

* Change default credentials in production
* Use read-only users for analytics
* Enable SSL and connection pooling for deployment environments

---

**Last Updated:** Jan 2026
