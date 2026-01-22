# Troubleshooting Guide

**Self-Healing MLOps Pipeline - Common Issues and Solutions**

---

## 📋 Table of Contents

- [Startup & Installation](#startup--installation)
- [Data Validation Issues](#data-validation-issues)
- [Model Loading & Training](#model-loading--training)
- [Drift Detection](#drift-detection)
- [Performance & Resource Issues](#performance--resource-issues)
- [Monitoring Problems](#monitoring-problems)

---

## 🚀 Startup & Installation

### Issue: `docker-compose up` Fails

**Error Messages:**
```
ERROR: Service 'mlflow' failed to start
permission denied: /var/run/docker.sock
```

**Solutions:**

1. **Docker not running:**
   ```bash
   # On Mac/Windows
   open -a Docker
   sleep 30
   docker-compose up
   ```

2. **Docker socket permission denied:**
   ```bash
   # On Linux
   sudo usermod -aG docker $USER
   newgrp docker
   docker-compose up
   ```

3. **Port already in use:**
   ```bash
   # Find what's using port 5000 (MLflow)
   lsof -i :5000

   # Kill process or change Docker port mapping
   # In docker-compose.yml: change "5000:5000" to "5001:5000"
   ```

---

### Issue: Python Dependencies Missing

**Error:**
```
ModuleNotFoundError: No module named 'mlflow'
```

**Solutions:**

1. **Install dev dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Verify Python version:**
   ```bash
   python --version  # Should be 3.10+
   ```

3. **Create fresh venv:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

### Issue: Pre-commit Hooks Prevent Commit

**Error:**
```
pre-commit hook failed: check-toml failed
```

**Solutions:**

1. **Run Black formatter:**
   ```bash
   black .
   ```

2. **Run linters:**
   ```bash
   flake8 .
   mypy src/
   ```

3. **Commit failing files:**
   ```bash
   git add .  # Re-add after fixes
   git commit -m "Fix formatting/linting"
   ```

4. **Skip hooks (NOT recommended):**
   ```bash
   git commit --no-verify
   ```

---

## 📊 Data Validation Issues

### Issue: Prediction Data Fails Validation

**Error:**
```
pandera.errors.SchemaError: Column 'age' failed validation with error:
expected float64, got int64
```

**Solutions:**

1. **Check data types:**
   ```python
   import pandas as pd
   df = pd.read_csv('predictions.csv')
   print(df.dtypes)
   ```

2. **Convert types:**
   ```python
   df['age'] = df['age'].astype('float64')
   ```

3. **Update schema in code:**
   - Edit: `src/storage/repositories.py`
   - Update the Pandera schema to match actual data

---

### Issue: Missing Values in Features

**Error:**
```
ValidationError: Column 'income' has 15 null values
```

**Solutions:**

1. **Check null count:**
   ```python
   df.isnull().sum()
   ```

2. **Handle nulls:**
   ```python
   # Drop nulls
   df = df.dropna()

   # Or impute
   df['income'].fillna(df['income'].median(), inplace=True)
   ```

3. **Update data pipeline:**
   - Ensure upstream system fills these fields
   - Or update Pandera schema to allow nulls

---

### Issue: Reference Data Mismatch

**Error:**
```
ValueError: Prediction feature set doesn't match reference
```

**Solutions:**

1. **Check reference data:**
   ```bash
   # View reference features
   python -c "
   import json
   with open('monitoring/reference/reference_metadata.json') as f:
       metadata = json.load(f)
       print('Features:', metadata['features'])
   "
   ```

2. **Regenerate reference:**
   ```bash
   make bootstrap
   ```

3. **Verify feature names match:**
   - Check for typos: `age` vs `Age`
   - Check for underscores: `max_income` vs `maxIncome`
   - Compare in: `src/utils/dataset_fingerprint.py`

---

## 🤖 Model Loading & Training

### Issue: Model Not Found in MLflow

**Error:**
```
FileNotFoundError: Model 'credit-risk-model' not found in registry
```

**Solutions:**

1. **List available models:**
   ```bash
   # Via MLflow UI
   open http://localhost:5000
   # Navigate to Models section
   ```

2. **Train initial model:**
   ```bash
   make train
   # This creates 'credit-risk-model' in MLflow
   ```

3. **Check model production stage:**
   - A model must be in "Production" stage to be used by API
   - In MLflow UI: Models → credit-risk-model → Versions → Transition to → Production

---

### Issue: GPU Out of Memory During Training

**Error:**
```
RuntimeError: CUDA out of memory
```

**Solutions:**

1. **Reduce batch size:**
   ```python
   # In src/train_model_mlflow.py
   BATCH_SIZE = 16  # From 32
   ```

2. **Use CPU instead:**
   ```bash
   # Set environment variable
   export CUDA_VISIBLE_DEVICES=""
   make train
   ```

3. **Monitor GPU usage:**
   ```bash
   nvidia-smi  # NVIDIA GPUs
   ```

---

### Issue: Training Takes Too Long

**Symptoms:**
- Training running > 30 minutes
- No progress in logs

**Solutions:**

1. **Check logs:**
   ```bash
   docker-compose logs trainer
   ```

2. **Reduce data size (temporary):**
   ```python
   # In training script
   df = df.head(10000)  # Use 10k samples instead of full
   ```

3. **Parallelize training:**
   - Edit: `src/train_model_mlflow.py`
   - Add `n_jobs=-1` to model constructors
   - Increases CPU usage but speeds up training

---

## 📉 Drift Detection

### Issue: Drift Detection Reports Missing

**Error:**
```
FileNotFoundError: No drift reports found in monitoring/reports/drift_reports/
```

**Solutions:**

1. **Trigger monitoring job:**
   ```bash
   docker-compose up monitoring
   # Wait 1-2 minutes for report generation
   ```

2. **Check monitoring logs:**
   ```bash
   docker-compose logs monitoring
   ```

3. **Verify reference data exists:**
   ```bash
   ls -lh monitoring/reference/
   # Should contain: reference_data.csv, reference_metadata.json
   ```

4. **Generate test data first:**
   ```bash
   make generate-predictions
   # Creates sample predictions to analyze
   ```

---

### Issue: High False Positive Drift Detections

**Symptoms:**
- Drift detected every day
- But actual data looks similar

**Solutions:**

1. **Adjust drift thresholds:**
   - Edit: `src/analytics/drift_detection.py`
   - Increase `p_value_threshold` from 0.05 to 0.10
   - Increase `effect_size_threshold` from 0.3 to 0.5

2. **Review drift method:**
   - Kolmogorov-Smirnov test sensitive to small shifts
   - Consider: Wasserstein distance, Population Stability Index

3. **Expand reference window:**
   - Use more reference data (larger sample)
   - Edit: `scripts/bootstrap_reference.py`
   - Increase reference sample size

---

### Issue: Drift Detector Crashes

**Error:**
```
IndexError: Number of features mismatch
```

**Solutions:**

1. **Check feature consistency:**
   ```python
   # In monitoring job
   prediction_df = pd.read_csv('monitoring/predictions/predictions.csv')
   print("Columns:", prediction_df.columns.tolist())
   ```

2. **Regenerate reference:**
   ```bash
   make bootstrap
   ```

3. **Verify feature engineering:**
   - Check: `src/utils/dataset_fingerprint.py`
   - Ensure all predictions match reference feature set

---

## ⚡ Performance & Resource Issues

### Issue: High Memory Usage

**Symptoms:**
```
MemoryError: Unable to allocate memory
```

**Solutions:**

1. **Check memory usage:**
   ```bash
   docker stats
   ```

2. **Reduce batch size:**
   - Edit service config (Dockerfile, docker-compose.yml)
   - Reduce BATCH_SIZE variable

3. **Clean old artifacts:**
   ```bash
   make clean-mlflow  # Removes old MLflow runs
   ```

4. **Limit monitoring lookback:**
   - Edit: `src/monitoring/monitoring_job.py`
   - Reduce lookback_days from 30 to 7

---

### Issue: API Response Times Slow (> 500ms)

**Symptoms:**
- Predictions take > 1 second
- Users report timeout

**Solutions:**

1. **Profile API:**
   ```bash
   # Add timing to src/api_mlflow.py
   import time
   start = time.time()
   # prediction code
   print(f"Prediction took {time.time() - start}s")
   ```

2. **Check model size:**
   ```bash
   du -sh mlflow/artifacts/*/
   # Large models (> 500MB) need optimization
   ```

3. **Use model quantization:**
   - Replace float64 with float32
   - Reduces size and latency

4. **Scale API:**
   ```bash
   # In docker-compose.yml, scale API service
   docker-compose up --scale api=3
   ```

---

### Issue: Disk Space Running Out

**Symptoms:**
```
OSError: No space left on device
```

**Solutions:**

1. **Check disk usage:**
   ```bash
   du -sh monitoring/ mlflow/ models/
   ```

2. **Archive old artifacts:**
   ```bash
   # Move old reports
   tar -czf reports_archive_$(date +%Y%m%d).tar.gz \
       monitoring/reports/drift_reports/
   rm -rf monitoring/reports/drift_reports/*
   ```

3. **Clean MLflow:**
   ```bash
   # Remove old experiment runs
   docker-compose exec mlflow sqlite3 mlflow/mlflow.db \
       "DELETE FROM runs WHERE end_time < datetime('now', '-30 days')"
   ```

4. **Limit monitoring retention:**
   - Edit: `src/monitoring/monitoring_job.py`
   - Add: `df = df.tail(100000)` to limit stored predictions

---

## 🔍 Monitoring Problems

### Issue: Monitoring Job Not Running

**Error:**
```
Container 'monitoring' exited with code 1
```

**Solutions:**

1. **Check logs:**
   ```bash
   docker-compose logs monitoring | tail -100
   ```

2. **Common causes:**
   - Missing predictions CSV
   - Reference data not generated
   - Database connection failed

3. **Restart monitoring:**
   ```bash
   docker-compose restart monitoring
   sleep 5
   ```

---

### Issue: Labels Not Aligning with Predictions

**Symptoms:**
- Prediction count: 1000
- Label count: 50
- Most predictions have no true label

**This is EXPECTED behavior.** Labels arrive delayed in real-world systems.

**Solutions:**

1. **Check label timeline:**
   ```bash
   # Count labels per day
   python -c "
   import pandas as pd
   labels = pd.read_csv('monitoring/labels/labels.csv')
   labels['date'] = pd.to_datetime(labels['label_timestamp']).dt.date
   print(labels.groupby('date').size())
   "
   ```

2. **Generate sample labels:**
   ```bash
   make generate-predictions
   # Includes sample labels
   ```

3. **Manual label ingestion:**
   ```bash
   # Append to monitoring/labels/labels.csv
   # Format: prediction_id,true_label,label_timestamp,label_source
   ```

---

### Issue: Evaluation Gate Rejecting All Models

**Symptoms:**
- Retraining runs but always rejected
- Never promotes to production

**Solutions:**

1. **Review gate criteria:**
   ```bash
   open src/retraining/evaluation_gate.py
   ```

2. **Check baseline model:**
   - If baseline F1 = 0.95, gate requires >= 0.97 (2% improvement)
   - If limited training data, gate may be impossible to satisfy

3. **Adjust gates (temporary testing):**
   ```python
   gate = EvaluationGate(
       min_f1_improvement_pct=0.0,  # Disabled for testing
       max_brier_degradation=1.0,    # Disabled for testing
   )
   ```

4. **Document lower gates:**
   - Update runbook with new thresholds
   - Add comment explaining why gates were lowered

---

## 🔧 How to Get Help

### Collecting Debug Information

When reporting issues, collect:

```bash
# System info
python --version
docker --version
docker-compose --version

# Service status
make health

# Last logs
docker-compose logs --tail=100 > service_logs.txt

# Data status
wc -l monitoring/predictions/predictions.csv
wc -l monitoring/labels/labels.csv

# Disk usage
du -sh . monitoring/ mlflow/
```

### Diagnostic Commands

```bash
# Check all services
docker-compose ps

# View all logs
docker-compose logs | tail -200

# Test API
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"age": 25, "income": 50000, ...}'

# Check MLflow
curl http://localhost:5000/health

# Verify monitoring
ls -lt monitoring/reports/drift_reports/ | head -3
```

---

## 📞 When to Contact Support

- **Installation issues**: Run `make verify` and share output
- **Data validation**: Share sample CSV and validation error
- **Model training**: Share training logs from `docker-compose logs trainer`
- **Drift detection**: Share drift report and prediction statistics

---

**Last Updated:** January 2024
**Version:** 1.0
