
# Self-Healing MLOps Pipeline

## Phase 1 — Foundation: Prediction Service

This repository contains **Phase 1** of a multi-phase **Self-Healing MLOps Pipeline**.

The objective of this phase is **not** to build a self-healing system yet.
Instead, Phase 1 focuses on creating a **correct, reproducible, and observable ML prediction system** that later phases can safely extend with monitoring, drift diagnosis, and controlled retraining.

---

## 🎯 Phase 1 Objectives

Phase 1 is intentionally limited in scope. Its purpose is to establish engineering discipline and system correctness.

This phase ensures:

* Deterministic data loading
* Frozen preprocessing shared between training and inference
* Explicit feature schema preservation
* Versioned model artifacts
* FastAPI-based prediction service
* Input validation with Pydantic
* Time-stamped prediction logging
* Reproducible execution

---

## 🚫 What This Phase Does *Not* Do

The following are **explicitly out of scope** for Phase 1:

* No drift detection
* No automated retraining
* No self-healing logic
* No production performance claims
* No accuracy optimization focus

These are deferred intentionally to avoid premature automation and incorrect system design.

---

## 📊 Dataset

**Give Me Some Credit (Kaggle)** — credit risk / default prediction dataset.

**Why it is used here:**

* Tabular, structured data
* Clear binary target
* Suitable for learning pipeline discipline

**Known limitations (acknowledged):**

* Static snapshot (no event-level timestamps)
* No natural delayed labels
* Limited realism for long-term drift analysis

This dataset is used **only for early phases** to build infrastructure.
Later phases will switch to temporally realistic datasets.

---

## 🧱 Project Structure

```
self-healing-mlops/
├── src/
│   ├── data.py              # Data loading logic
│   ├── preprocessing.py     # Frozen preprocessing pipeline
│   ├── train.py             # Model training + artifact creation
│   ├── predict.py           # Shared inference logic
│   └── api.py               # FastAPI prediction service
│
├── requirements.txt
├── README.md
```

> Note:
>
> * Raw data, trained artifacts, logs, and virtual environments are intentionally excluded from version control.

---

## ⚙️ Setup

### 1. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🏋️ Train the Model

```bash
python src/train.py
```

This step:

* Loads data
* Applies frozen preprocessing
* Trains the model
* Saves artifacts (model, preprocessing, schema, metadata)

---

## 🚀 Run the API

```bash
uvicorn src.api:app --reload
```

### Endpoints

* Health check:

  ```
  GET /health
  ```
* Prediction:

  ```
  POST /predict
  ```

Interactive API docs:

```
http://localhost:8000/docs
```

---

## 🔮 Example Prediction Request

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "RevolvingUtilizationOfUnsecuredLines": 0.7,
    "age": 45,
    "NumberOfTime30-59DaysPastDueNotWorse": 1,
    "DebtRatio": 0.5,
    "MonthlyIncome": 6000,
    "NumberOfOpenCreditLinesAndLoans": 8,
    "NumberOfTimes90DaysLate": 0,
    "NumberRealEstateLoansOrLines": 1,
    "NumberOfTime60-89DaysPastDueNotWorse": 0,
    "NumberOfDependents": 2
  }'
```

---

## 🧠 Design Principles

This project prioritizes:

* **Correctness over cleverness**
* **Observability before automation**
* **Diagnosis before action**
* **Explicit constraints over hidden assumptions**

Retraining, drift detection, and “self-healing” behavior are meaningless without a reliable foundation.

---

## 🛣️ Roadmap

* **Phase 1 (current)**
  Prediction service with reproducible artifacts and observability

* **Phase 2**
  Structured logging and monitoring-ready data collection

* **Phase 3**
  Drift detection and diagnosis (data drift vs concept drift)

* **Phase 4**
  Controlled retraining decisions (no naïve auto-retrain)

* **Phase 5**
  Dataset evolution and validation on temporally realistic data

---

## 📌 Status

**Phase 1: Complete**

This repository represents a **foundation**, not a finished system.

Subsequent phases will build incrementally on top of this base without breaking backward compatibility or system guarantees.

---
