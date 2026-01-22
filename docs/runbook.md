# Operations Runbook

**Self-Healing MLOps Pipeline - Day-to-Day Operations Guide**

---

## 📋 Table of Contents

- [Daily Operations](#daily-operations)
- [Weekly Maintenance](#weekly-maintenance)
- [Emergency Procedures](#emergency-procedures)
- [Monitoring & Alerts](#monitoring--alerts)
- [Common Tasks](#common-tasks)

---

## 🔄 Daily Operations

### Morning Checklist

```bash
# 1. Check service health
make health

# 2. Review overnight monitoring
make logs-monitoring | tail -100

# 3. Check prediction volume
curl http://localhost:8000/monitoring/stats | jq

# 4. Verify MLflow
open http://localhost:5000
```

### Expected Healthy State

| Service | Status | Check |
|---------|--------|-------|
| MLflow | Running | http://localhost:5000/health |
| API | Running | http://localhost:8000/health |
| Monitoring | Running | `docker-compose ps monitoring` |

### Key Metrics to Monitor

**Prediction Volume:**
- Expected: 100-1000 predictions/day
- Alert if: < 10 predictions/hour (service issue)
- Alert if: > 10,000 predictions/hour (unusual traffic)

**Drift Score:**
- Normal: 0-30% features drifted
- Warning: 30-50% features drifted
- Critical: > 50% features drifted

**Model Performance:**
- F1 Score: Should be ≥ baseline (check MLflow)
- Brier Score: Should be ≤ 0.20

---

## 📅 Weekly Maintenance

### Monday: Review Drift Reports

```bash
# Check latest drift reports
ls -lt monitoring/reports/drift_reports/ | head -5

# Open latest report
open $(ls -t monitoring/reports/drift_reports/*.html | head -1)
```

**What to look for:**
- Consistent drift in same features → Investigate cause
- Sudden drift spike → Check data pipeline
- No drift for weeks → Verify monitoring is running

### Wednesday: Model Performance Review

```bash
# Check MLflow for recent runs
open http://localhost:5000

# Compare production vs staging models
# Navigate to: Models → credit-risk-model
```

**Actions:**
- If staging model exists → Review evaluation gate results
- If production model is > 30 days old → Consider retraining
- Document any performance trends

### Friday: Cleanup & Backup

```bash
# Archive old reports (optional)
tar -czf reports_backup_$(date +%Y%m%d).tar.gz monitoring/reports/

# Check disk usage
du -sh monitoring/ mlflow/ models/

# Clean old artifacts if > 10GB
# (Manual review before deletion)
```

---

## 🚨 Emergency Procedures

### API is Down

**Symptoms:**
- `make health` shows API ✗
- Users cannot get predictions

**Steps:**
1. Check logs:
   ```bash
   make logs-api
   ```

2. Common causes:
   - Model not loaded → Check MLflow (model must be in Production)
   - Container crashed → Restart: `docker-compose restart api`
   - Port conflict → Check: `lsof -i :8000`

3. Restart API:
   ```bash
   docker-compose restart api
   sleep 5
   make health
   ```

4. If still failing:
   ```bash
   docker-compose logs api > api_error.log
   # Send log to team for analysis
   ```

### MLflow is Down

**Symptoms:**
- Cannot access http://localhost:5000
- API logs show MLflow connection errors

**Steps:**
1. Restart MLflow:
   ```bash
   docker-compose restart mlflow
   sleep 10
   ```

2. Check database:
   ```bash
   ls -lh mlflow/mlflow.db
   # Should exist and have recent modification time
   ```

3. If database corrupted:
   ```bash
   # CAUTION: This loses experiment history
   docker-compose down
   mv mlflow mlflow_backup_$(date +%Y%m%d)
   docker-compose up -d mlflow
   ```

### High Drift Alert

**Symptoms:**
- Drift share > 50%
- Multiple features showing drift

**Steps:**
1. Review drift report:
   ```bash
   open $(ls -t monitoring/reports/drift_reports/*.html | head -1)
   ```

2. Identify drifted features:
   - Check which features drifted
   - Compare distributions (histograms in report)

3. Investigate cause:
   - Data pipeline change?
   - Upstream system modification?
   - Genuine population shift?

4. Decision:
   - **If data issue** → Fix pipeline, don't retrain
   - **If genuine drift** → Trigger retraining
   - **If unsure** → Escalate to data science team

### Retraining Failure

**Symptoms:**
- Shadow model training failed
- Airflow DAG shows error

**Steps:**
1. Check Airflow logs:
   ```bash
   docker-compose logs airflow
   ```

2. Common issues:
   - Insufficient labeled data → Wait for more labels
   - Data validation failed → Check Pandera schemas
   - Evaluation gate rejected → Review gate criteria

3. Manual retraining:
   ```bash
   docker-compose up trainer
   # Monitor progress
   ```

---

## 📊 Monitoring & Alerts

### What to Monitor

**System Health:**
- Service uptime (API, MLflow, Monitoring)
- Container resource usage (CPU, memory)
- Disk space (monitoring/, mlflow/)

**Data Quality:**
- Prediction volume
- Missing values in features
- Outliers in input data

**Model Performance:**
- Proxy metrics (prediction distribution)
- Drift score
- True performance (when labels available)

### Alert Thresholds (Recommended)

| Metric | Warning | Critical |
|--------|---------|----------|
| API Response Time | > 500ms | > 2s |
| Prediction Volume | < 50/hour | < 10/hour |
| Drift Share | > 30% | > 50% |
| F1 Score | < baseline - 5% | < baseline - 10% |
| Disk Space | > 80% | > 95% |

### Setting Up Alerts

*Implementation depends on monitoring stack (Prometheus, Datadog, etc.)*

Example with email alerts:
```bash
# Add to monitoring job
if [ "$drift_share" -gt "50" ]; then
    echo "High drift detected" | mail -s "MLOps Alert" team@company.com
fi
```

---

## 🛠️ Common Tasks

### Task 1: Add New Labeled Data

**When:** Labels arrive for past predictions

**Steps:**
```bash
# 1. Prepare labels CSV
# Format: prediction_id, true_label, label_timestamp, label_source

# 2. Append to labels store
cat new_labels.csv >> monitoring/labels/labels.csv

# 3. Verify
wc -l monitoring/labels/labels.csv
```

### Task 2: Manually Trigger Retraining

**When:** Drift is high and you want to retrain immediately

**Steps:**
```bash
# Option 1: Via Airflow
docker-compose exec airflow airflow dags trigger retraining_pipeline

# Option 2: Direct training
make train

# Option 3: Via Makefile (full workflow)
make quick-test  # Generates data and triggers monitoring
```

### Task 3: Rollback to Previous Model

**When:** New production model is performing poorly

**Steps:**
1. Go to MLflow UI: http://localhost:5000
2. Navigate to: Models → credit-risk-model
3. Find previous production version (now in "Archived")
4. Click: "Transition to → Production"
5. Restart API:
   ```bash
   docker-compose restart api
   ```

### Task 4: Update Evaluation Gate Criteria

**When:** Gate is too strict/lenient

**Steps:**
1. Edit `src/retraining/evaluation_gate.py`:
   ```python
   gate = EvaluationGate(
       min_f1_improvement_pct=3.0,  # Changed from 2.0
       max_brier_degradation=0.005, # Stricter
   )
   ```

2. Rebuild services:
   ```bash
   make rebuild
   ```

3. Document change in runbook

### Task 5: Export Monitoring Data

**When:** For analysis or reporting

**Steps:**
```bash
# Export predictions
cp monitoring/predictions/predictions.csv \
   exports/predictions_$(date +%Y%m%d).csv

# Export monitoring results
tar -czf exports/monitoring_$(date +%Y%m%d).tar.gz \
    monitoring/metrics/monitoring_results/

# Export drift reports
tar -czf exports/drift_reports_$(date +%Y%m%d).tar.gz \
    monitoring/reports/drift_reports/
```

---

## 📞 Escalation Contacts

| Issue | Contact | Response Time |
|-------|---------|---------------|
| Production API Down | On-call engineer | Immediate |
| High Drift Alert | Data Science Lead | 4 hours |
| Model Performance | ML Engineer | Next business day |
| Infrastructure | DevOps Team | 2 hours |

---

## 📚 Additional Resources

- [Troubleshooting Guide](troubleshooting.md)
- [Architecture Documentation](architecture.md)
- [API Reference](api.md)
- [Evaluation Gate Criteria](evaluation_gates.md)

---

**Last Updated:** January 2024
**Owner:** MLOps Team
**Review Cycle:** Monthly
