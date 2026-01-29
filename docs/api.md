# API Reference

## Base URL

```
http://localhost:8000
```

---

## Endpoints

### Health & Info

#### `GET /`

Service status.

```json
{
  "service": "Self-Healing MLOps Prediction API",
  "version": "1.0.0",
  "status": "running"
}
```

#### `GET /health`

API and model health.

```json
{
  "status": "healthy",
  "model_loaded": true,
  "mlflow_connected": true,
  "prediction_logger_ready": true
}
```

#### `GET /model/info`

Loaded model metadata.

```json
{
  "model_version": "1",
  "model_type": "LogisticRegression",
  "training_date": "2024-01-15T10:30:00",
  "artifact_path": "models/1/artifacts/model.pkl",
  "input_features": ["age", "MonthlyIncome", "..."]
}
```

---

### Predictions

#### `POST /predict`

Single prediction.

**Request**

```json
{
  "age": 45,
  "MonthlyIncome": 9120.0,
  "DebtRatio": 0.80,
  "...": "other features"
}
```

**Response**

```json
{
  "prediction": 0,
  "probability": 0.0872,
  "model_version": "1",
  "prediction_id": "pred_20240115_143022",
  "timestamp": "2024-01-15T14:30:22"
}
```

**Status Codes**

* `200` OK
* `422` Invalid input
* `503` Model not loaded

---

#### `POST /predict/batch`

Batch predictions.

**Request**

```json
[{ "...": "features" }, { "...": "features" }]
```

**Response**

```json
[
  {
    "prediction": 0,
    "probability": 0.0872,
    "prediction_id": "pred_20240115_143022"
  }
]
```

---

### Monitoring

#### `GET /monitoring/stats`

Prediction statistics.

```json
{
  "total_predictions": 1250,
  "predictions_24h": 450,
  "average_probability": 0.1234,
  "class_balance": {
    "negative": 0.92,
    "positive": 0.08
  }
}
```

---

## Errors

```json
// 422 Validation Error
{ "detail": "Invalid input" }

// 503 Model Not Loaded
{ "detail": "Model not loaded" }

// 500 Internal Error
{ "detail": "Internal server error" }
```

---

## Logging

All predictions are logged to:

```
monitoring/predictions/predictions.csv
```

Logged fields: timestamp, prediction_id, prediction, probability, model_version, input features.

---

## Authentication & Rate Limiting

Not enabled (development mode).
Recommended for production:

* Token auth (`HTTPBearer`)
* Rate limiting (`slowapi`)

---

## Performance

* Single prediction: **10–20 ms**
* Batch (100): **50–100 ms**
* ~400 req/sec with Gunicorn (4 workers)

---

## Versioning

Model version can be specified:

```
POST /predict?model_version=2
```

---

## Docs

Swagger UI:

```
http://localhost:8000/docs
```

---

## Support

* `troubleshooting.md`
* `architecture.md`
* GitHub Issues
