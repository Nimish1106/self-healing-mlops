# API Reference

## Base URL

```
http://localhost:8000
```

## Endpoints

### 1. Root

```http
GET /
```

Returns service information and status.

**Response:**
```json
{
  "service": "Self-Healing MLOps Prediction API",
  "version": "1.0.0",
  "status": "running"
}
```

---

### 2. Health Check

```http
GET /health
```

Returns service and model health status.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "mlflow_connected": true,
  "prediction_logger_ready": true
}
```

---

### 3. Model Info

```http
GET /model/info
```

Returns information about the currently loaded model.

**Response:**
```json
{
  "model_version": "1",
  "model_type": "LogisticRegression",
  "training_date": "2024-01-15T10:30:00",
  "artifact_path": "models/1/artifacts/model.pkl",
  "input_features": [
    "RevolvingUtilizationOfUnsecuredLines",
    "age",
    "NumberOfTime30_59DaysPastDueNotWorse",
    "DebtRatio",
    "MonthlyIncome",
    "NumberOfOpenCreditLinesAndLoans",
    "NumberOfTimes90DaysLate",
    "NumberRealEstateLoansOrLines",
    "NumberOfTime60_89DaysPastDueNotWorse",
    "NumberOfDependents"
  ]
}
```

---

### 4. Make Prediction

```http
POST /predict
Content-Type: application/json
```

Make a prediction for a single instance.

**Request Body:**
```json
{
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
}
```

**Response:**
```json
{
  "prediction": 0,
  "probability": 0.0872,
  "model_version": "1",
  "prediction_id": "pred_20240115_143022",
  "timestamp": "2024-01-15T14:30:22"
}
```

**Status Codes:**
- `200` - Successful prediction
- `422` - Validation error (invalid input)
- `503` - Model not loaded

---

### 5. Batch Predictions

```http
POST /predict/batch
Content-Type: application/json
```

Make predictions for multiple instances.

**Request Body:**
```json
[
  {
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
  },
  {
    "RevolvingUtilizationOfUnsecuredLines": 0.5,
    "age": 35,
    "NumberOfTime30_59DaysPastDueNotWorse": 0,
    "DebtRatio": 0.5,
    "MonthlyIncome": 5000.0,
    "NumberOfOpenCreditLinesAndLoans": 10,
    "NumberOfTimes90DaysLate": 0,
    "NumberRealEstateLoansOrLines": 3,
    "NumberOfTime60_89DaysPastDueNotWorse": 0,
    "NumberOfDependents": 1
  }
]
```

**Response:**
```json
[
  {
    "prediction": 0,
    "probability": 0.0872,
    "model_version": "1",
    "prediction_id": "pred_20240115_143022",
    "timestamp": "2024-01-15T14:30:22"
  },
  {
    "prediction": 0,
    "probability": 0.0456,
    "model_version": "1",
    "prediction_id": "pred_20240115_143023",
    "timestamp": "2024-01-15T14:30:23"
  }
]
```

---

### 6. Monitoring Stats

```http
GET /monitoring/stats
```

Returns monitoring statistics for current predictions.

**Response:**
```json
{
  "total_predictions": 1250,
  "predictions_24h": 450,
  "average_probability": 0.1234,
  "prediction_distribution": {
    "0": 1150,
    "1": 100
  },
  "class_balance": {
    "negative_class_ratio": 0.92,
    "positive_class_ratio": 0.08
  }
}
```

---

## Error Responses

### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "age"],
      "msg": "ensure this value is greater than or equal to 18",
      "type": "value_error.number.not_ge",
      "ctx": {"limit_value": 18}
    }
  ]
}
```

### Model Not Loaded (503)

```json
{
  "detail": "Model not loaded. Please try again later."
}
```

### Internal Server Error (500)

```json
{
  "detail": "Internal server error. Check logs for details."
}
```

---

## Authentication

Currently, the API has **no authentication**. In production, add:

```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/predict")
async def predict(request: PredictionRequest, credentials: HTTPAuthCredentials = Depends(security)):
    # Validate token
    pass
```

---

## Rate Limiting

Currently, the API has **no rate limiting**. In production, add:

```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/predict")
@limiter.limit("100/minute")
async def predict(request: PredictionRequest):
    pass
```

---

## Logging

All predictions are automatically logged to:
```
monitoring/predictions/predictions.csv
```

Each prediction record includes:
- timestamp
- prediction_id
- prediction
- probability
- model_version
- all input features

---

## Examples

### Using cURL

```bash
# Single prediction
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

### Using Python Requests

```python
import requests

url = "http://localhost:8000/predict"
features = {
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
}

response = requests.post(url, json=features)
print(response.json())
```

### Using Python SDK

```python
from src.api_mlflow import PredictionRequest

client = PredictionRequest(
    RevolvingUtilizationOfUnsecuredLines=0.766127,
    age=45,
    NumberOfTime30_59DaysPastDueNotWorse=2,
    DebtRatio=0.802982,
    MonthlyIncome=9120.0,
    NumberOfOpenCreditLinesAndLoans=13,
    NumberOfTimes90DaysLate=0,
    NumberRealEstateLoansOrLines=6,
    NumberOfTime60_89DaysPastDueNotWorse=0,
    NumberOfDependents=2
)

# Load model and make prediction locally
# prediction = make_prediction(client)
```

---

## Performance Considerations

### Latency
- Single prediction: ~10-20ms
- Batch predictions (100): ~50-100ms

### Throughput
- Single-threaded: ~100 requests/sec
- With gunicorn (4 workers): ~400 requests/sec

### Scaling
For higher throughput, use:
```bash
gunicorn src.api_mlflow:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

---

## Versioning

The API uses model versioning via MLflow:

```http
POST /predict?model_version=2
```

This allows A/B testing of models.

---

## OpenAPI Specification

Interactive documentation available at:
```
http://localhost:8000/docs
```

Swagger UI for testing endpoints.

---

## Support

For issues or questions:
1. Check [Troubleshooting Guide](troubleshooting.md)
2. Review [Architecture Documentation](architecture.md)
3. Open an issue on GitHub
