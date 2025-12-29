
## 💡 Key Concepts

### 1️⃣ Frozen Reference Data

<table>
<tr>
<td width="20%"><b>What</b></td>
<td>Training test set snapshot (last 20% of data)</td>
</tr>
<tr>
<td><b>Why</b></td>
<td>Drift is relative to this baseline</td>
</tr>
<tr>
<td><b>Status</b></td>
<td><code>IMMUTABLE</code> - Never modified after creation</td>
</tr>
<tr>
<td><b>Integrity</b></td>
<td>SHA256 hash verified on every monitoring run</td>
</tr>
</table>

```bash
# Re-bootstrap if needed (⚠️ destroys old reference)
docker-compose run --rm bootstrap
```

---

### 2️⃣ Minimum Sample Requirement

<div align="center">

![Min Samples](https://img.shields.io/badge/Minimum_Samples-200-critical?style=for-the-badge)

</div>

**Why 200?**
- Statistical tests (KS, Chi-squared) need adequate power
- Central Limit Theorem validity
- Prevents false positives/negatives

**Below threshold:**
```json
{
  "status": "insufficient_data",
  "num_predictions": 87,
  "min_required": 200,
  "message": "Waiting for more predictions"
}
```

---

### 3️⃣ Proxy Metrics (No Labels Needed)

<table>
<tr>
<th>Metric</th>
<th>What It Measures</th>
<th>Why It Matters</th>
</tr>
<tr>
<td>📊 Prediction Distribution</td>
<td>Positive rate, probability stats</td>
<td>Detects output behavior changes</td>
</tr>
<tr>
<td>🎲 Probability Entropy</td>
<td>Model decisiveness</td>
<td>High entropy = uncertain predictions</td>
</tr>
<tr>
<td>⏱️ Time-Windowed Trends</td>
<td>1h, 6h, 24h windows</td>
<td>Detect sudden vs gradual changes</td>
</tr>
<tr>
<td>📈 Rate of Change</td>
<td>How fast metrics shift</td>
<td>Urgency indicator</td>
</tr>
</table>

**❌ Not Included:** Accuracy, Precision, Recall (require labels)

---

### 4️⃣ Drift Detection

<div align="center">

### 🎯 What Drift Tells Us

| ✅ What Evidently Detects | ❌ What It Does NOT Tell |
|---------------------------|--------------------------|
| Feature distributions changed | Model is wrong |
| Statistical test results | Need to retrain |
| Which features drifted | Change is "bad" |

</div>

<br/>

> **⚠️ Critical Understanding**  
> **Drift ≠ Model Failure**

<br/>

**Possible Interpretations:**

| Scenario | Interpretation | Action |
|----------|----------------|--------|
| 🌍 World changed | Model might be outdated | Consider retraining (Phase 4) |
| 🔧 Data quality issue | Pipeline problem | Fix data, not model |
| 📅 Seasonality | Expected variation | No action needed |
| 👥 New segment | Working as designed | Model is fine |

---

### 5️⃣ Observation vs Action

<table>
<tr>
<td width="50%" bgcolor="#E3F2FD">

### 📊 Phase 3 (Current)
**Observes & Reports**

- ✅ Logs predictions
- ✅ Computes statistics
- ✅ Detects drift
- ✅ Generates reports
- ✅ Creates signals

</td>
<td width="50%" bgcolor="#FFF3E0">

### 🚀 Phase 4 (Next)
**Decides & Acts**

- 🔄 Evaluates signals
- 🔄 Trains shadow models
- 🔄 Runs evaluation gates
- 🔄 Promotes models
- 🔄 Automated retraining

</td>
</tr>
</table>

---

## ⚙️ Configuration

### Environment Variables

Edit `docker-compose.yml`:

```yaml
monitoring:
  environment:
    - MONITORING_INTERVAL=300    # Seconds between runs
    - MONITORING_LOOKBACK=24     # Hours of data to analyze
```

### 📊 Recommended Settings

<table>
<tr>
<th>Prediction Volume</th>
<th>Interval</th>
<th>Lookback</th>
<th>Rationale</th>
</tr>
<tr>
<td>🐌 Low (<100/day)</td>
<td>3600s (1h)</td>
<td>168h (7d)</td>
<td>Need longer window for stats</td>
</tr>
<tr>
<td>🚶 Medium (100-1K/day)</td>
<td>600s (10m)</td>
<td>24h</td>
<td>Balance responsiveness & validity</td>
</tr>
<tr>
<td>🚀 High (>1K/day)</td>
<td>300s (5m)</td>
<td>6h</td>
<td>Fast drift detection possible</td>
</tr>
</table>

---

## 🌐 API Endpoints

<table>
<tr>
<th>Endpoint</th>
<th>Method</th>
<th>Purpose</th>
<th>Status</th>
</tr>
<tr>
<td><code>/</code></td>
<td>GET</td>
<td>Basic health check</td>
<td>✅ Public</td>
</tr>
<tr>
<td><code>/health</code></td>
<td>GET</td>
<td>Detailed status + prediction count</td>
<td>✅ Public</td>
</tr>
<tr>
<td><code>/model/info</code></td>
<td>GET</td>
<td>Current model metadata</td>
<td>✅ Public</td>
</tr>
<tr>
<td><code>/predict</code></td>
<td>POST</td>
<td>Make prediction + log</td>
<td>⭐ Primary</td>
</tr>
<tr>
<td><code>/monitoring/stats</code></td>
<td>GET</td>
<td>Quick stats (last 100)</td>
<td>📊 Monitoring</td>
</tr>
</table>

### Example Request

```bash
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

### Example Response

```json
{
  "prediction": 0,
  "probability": 0.087,
  "model_version": "1",
  "prediction_id": "pred_20240115_143022_123456",
  "timestamp": "2024-01-15T14:30:22.123456"
}
```

---

## 📊 Monitoring Outputs

### JSON Results

```json
{
  "timestamp": "2024-01-15T14:30:00",
  "analysis_window": {
    "lookback_hours": 24,
    "start_time": "2024-01-14T14:30:00",
    "end_time": "2024-01-15T14:30:00",
    "num_predictions": 1247
  },
  "proxy_metrics": {
    "overall_stats": {
      "positive_rate": 0.073,
      "probability_mean": 0.089,
      "probability_std": 0.142
    },
    "entropy": 1.23,
    "time_windowed": {
      "window_1H": {"positive_rate": 0.075},
      "window_6H": {"positive_rate": 0.072},
      "window_24H": {"positive_rate": 0.073}
    }
  },
  "drift_detection": {
    "drift_share": 0.30,
    "num_drifted_features": 3,
    "num_features_total": 10,
    "feature_drift_details": [
      {
        "feature": "MonthlyIncome",
        "drift_detected": true,
        "drift_score": 0.045,
        "stat_test": "ks"
      }
    ]
  }
}
```

### 📄 HTML Reports

**Location:** `monitoring/reports/drift_reports/drift_report_*.html`

**Contents:**
- 📊 Per-feature drift analysis
- 📈 Distribution comparisons (histograms)
- 📉 Statistical test results
- 🎨 Interactive visualizations

```bash
# Open latest report
open $(ls -t monitoring/reports/drift_reports/*.html | head -1)
```

---

## ✅ Verification

### Automated Check Script

```bash
#!/bin/bash
echo "🔍 Phase 3 Verification"
echo "======================="

# 1. Services
echo -n "1. Services running... "
docker-compose ps | grep -q "Up" && echo "✅" || echo "❌"

# 2. Reference
echo -n "2. Reference exists... "
test -f monitoring/reference/reference_data.csv && echo "✅" || echo "❌"

# 3. Predictions
echo -n "3. Predictions logged... "
test $(wc -l < monitoring/predictions/predictions.csv) -gt 200 && echo "✅" || echo "❌"

# 4. Results
echo -n "4. Monitoring results... "
test -n "$(ls monitoring/metrics/monitoring_results/ 2>/dev/null)" && echo "✅" || echo "❌"

# 5. API health
echo -n "5. API healthy... "
curl -sf http://localhost:8000/health > /dev/null && echo "✅" || echo "❌"

echo "======================="
```

### Manual Checklist

- [ ] 🐳 All Docker services show "Up" status
- [ ] 📦 Reference data exists and has metadata
- [ ] 📝 Predictions CSV has 200+ lines
- [ ] 📊 Monitoring results directory not empty
- [ ] 🌐 API returns 200 on `/health`
- [ ] 🔍 No ERROR logs in monitoring service
- [ ] 📈 Drift reports generated in HTML
- [ ] ℹ️ Logs show INFO-level observations (not warnings)

---

## 🔧 Troubleshooting

### Issue: "Insufficient samples" error

<details>
<summary><b>Show solution</b></summary>

**Symptom:**
```json
{"status": "insufficient_data", "num_predictions": 87}
```

**Diagnosis:**
```bash
# Check current count
curl http://localhost:8000/monitoring/stats | jq '.total_predictions'
```

**Fix:**
```bash
# Generate more predictions (see Quick Start Step 5)
# Need at least 200 for statistical validity
```

</details>

---

### Issue: "Reference data not found"

<details>
<summary><b>Show solution</b></summary>

**Symptom:**
```
FileNotFoundError: Reference data not found
```

**Fix:**
```bash
# Bootstrap reference data
docker-compose run --rm bootstrap

# Verify creation
ls -la monitoring/reference/
```

</details>

---

### Issue: "Reference integrity check failed"

<details>
<summary><b>Show solution</b></summary>

**Symptom:**
```
ValueError: Reference data integrity check FAILED
```

**Cause:** reference_data.csv was accidentally modified

**Fix:**
```bash
# Re-bootstrap (⚠️ will overwrite existing reference)
docker-compose run --rm bootstrap

# Restart monitoring
docker-compose restart monitoring
```

</details>

---

### Issue: Monitoring service not running

<details>
<summary><b>Show solution</b></summary>

**Diagnosis:**
```bash
# Check status
docker-compose ps monitoring

# View logs
docker-compose logs --tail=100 monitoring
```

**Common Causes:**
1. Reference data not bootstrapped
2. MLflow not accessible
3. Code syntax error

**Fix:**
```bash
# Rebuild and restart
docker-compose up -d --build monitoring

# Follow logs
docker-compose logs -f monitoring
```

</details>

---

### Issue: No drift detected

<details>
<summary><b>Show solution</b></summary>

**Expected Behavior:** ✅ This is CORRECT

With static test data, you won't see drift. Drift requires:
- Actual distribution changes
- Different data sources
- Time-based variation

**To test drift detection:**
1. Modify input data distributions
2. Use different dataset segment
3. Wait for real production data variation

</details>

---

## 📚 Important Concepts

### Data Drift vs Concept Drift

<table>
<tr>
<th width="50%">📊 Data Drift (Covariate Shift)</th>
<th width="50%">🔄 Concept Drift</th>
</tr>
<tr>
<td>

**What changes:** Input features (X)

**Example:**
- Average income increases 20%
- Age distribution shifts older
- New geographic regions

**Phase 3 detects:** ✅ YES

</td>
<td>

**What changes:** X→Y relationship

**Example:**
- Credit score becomes less predictive
- Economic crisis changes default patterns
- Regulatory changes

**Phase 3 detects:** ❌ NO (needs labels)

</td>
</tr>
</table>

---

### Why No Accuracy Metrics?

<div align="center">

### ⏰ Labels Arrive Later

</div>

**Example Timeline:**
```
Day 1:  Make prediction (will they default?)
        ↓
Day 1:  Log prediction for monitoring ✅
        ↓
Month 6: Ground truth arrives (did they default?)
        ↓
Month 6: Compute accuracy (Phase 4+) ⏳
```

**Solution:** Phase 3 uses **proxy metrics** that work without labels.

**Phase 4** will add **delayed evaluation** when labels arrive.

---

## 📦 Dependencies

```txt
# Phase 3 Additions
evidently==0.4.11    # Drift detection framework
scipy==1.11.4        # Statistical tests
plotly==5.18.0       # Evidently visualizations

# See requirements.txt for full dependency list
```

---

## 🎮 Quick Commands

```bash
# 🚀 Start everything
docker-compose up -d

# 🔄 Restart service
docker-compose restart monitoring

# 🔨 Rebuild and restart
docker-compose up -d --build monitoring

# 📋 View logs
docker-compose logs -f monitoring

# ⚡ Force monitoring run
docker-compose exec monitoring python src/monitoring/monitoring_job.py

# 🔍 Check service status
docker-compose ps

# 🧹 Clean slate (⚠️ deletes data)
docker-compose down -v

# 📊 View latest results
ls -t monitoring/metrics/monitoring_results/*.json | head -1 | xargs cat | jq
```

---
