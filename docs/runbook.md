
# Operations Runbook

**Self-Healing MLOps Pipeline — Production Operations**

---

## 1. Daily Health Checks (5 minutes)

```bash
# Services
docker-compose ps

# API
curl http://localhost:8000/health

# Monitoring stats
curl http://localhost:8000/monitoring/stats

# Database
docker exec postgres-mlops psql -U mlops -d mlops -c "SELECT 1;"

# MLflow
curl http://localhost:5000/health
```

**Healthy State**

* All containers: `Up`
* API `/health`: `status=healthy`
* MLflow reachable
* No errors in monitoring logs

---

## 2. Key Metrics & Thresholds

| Metric            | Normal       | Warning | Critical | Action                |
| ----------------- | ------------ | ------- | -------- | --------------------- |
| Prediction volume | 100–1000/day | <50/hr  | <10/hr   | Check API + upstream  |
| Drift share       | <30%         | 30–50%  | >50%     | Investigate / retrain |
| F1 score          | ≥ baseline   | −5%     | −10%     | Rollback / retrain    |
| API latency       | <200ms       | >500ms  | >2s      | Restart / scale       |
| DB size           | <5GB         | >5GB    | >10GB    | Archive data          |
| Disk usage        | <80%         | >80%    | >95%     | Cleanup immediately   |

---

## 3. Common Failures & Fixes

### API Down

```bash
docker-compose ps api
docker-compose logs --tail=100 api
docker-compose restart api
curl http://localhost:8000/health
```

**Common causes**

* No model in Production → promote in MLflow
* DB connection error → restart Postgres
* OOM → increase Docker memory

---

### PostgreSQL Down

```bash
docker ps | grep postgres-mlops
docker logs postgres-mlops --tail=100
docker-compose restart postgres-mlops
```

If corrupted (last resort):

```bash
docker-compose down
docker volume rm self-healing-mlops_postgres-mlops-volume
docker-compose up -d postgres-mlops
# restore from backup
```

---

### MLflow Down

```bash
docker-compose logs --tail=100 mlflow
docker-compose restart mlflow
curl http://localhost:5000/health
```

If DB corrupted → recreate MLflow store (experiment history lost).

---

## 4. Drift Handling (>50%)

**Steps**

```bash
# Open latest drift report
ls -t monitoring/reports/drift_reports | head -1

# Inspect drifted features
jq '.drift_detection.drifted_features' monitoring/metrics/monitoring_results/*.json
```

**Decision**

```
Pipeline issue? → Fix pipeline (NO retraining)
Real distribution shift? → Trigger retraining
Expected/seasonal? → Document & monitor
```

**Trigger retraining**

```bash
docker exec airflow-scheduler airflow dags trigger retraining_pipeline
```

---

## 5. Retraining Failed

```bash
# Airflow UI
open http://localhost:8080

# Logs
docker exec airflow-scheduler airflow tasks logs retraining_pipeline <task> <run_id>
```

**Typical causes**

* Not enough labels (<200)
* Data validation failure
* Evaluation gate rejection

**Fallback**

```bash
docker-compose up trainer
# Promote manually in MLflow if valid
```

---

## 6. Rollback Model (Fast)

```bash
# MLflow UI
open http://localhost:5000

# Models → credit-risk-model
# Transition previous version to Production

docker-compose restart api
curl http://localhost:8000/model/info
```

Rollback should take **<5 minutes**.

---

## 7. Backup (Daily)

```bash
docker exec postgres-mlops pg_dump -U mlops mlops > backups/mlops_$(date +%Y%m%d).sql
gzip backups/mlops_*.sql
```

Keep last **30 days** only.

---

## 8. High-Level Monitoring Commands

```bash
docker stats --no-stream
df -h
du -sh monitoring/ mlflow/ models/
```

---

## 9. Escalation

| Issue             | Severity | Response  |
| ----------------- | -------- | --------- |
| API Down          | P0       | Immediate |
| DB Failure        | P0       | Immediate |
| Drift >50%        | P1       | <4 hours  |
| Model degradation | P2       | Next day  |

**Escalation path**

```
On-call → Team Lead → Engineering Manager
```

---

## References

* `api.md`
* `database.md`
* `architecture.md`
* `troubleshooting.md`

---

**Last Updated:** Jan 2026
