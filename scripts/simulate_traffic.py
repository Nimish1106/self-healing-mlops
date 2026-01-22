"""
Simulate API traffic and delayed labels.
"""
import requests
import pandas as pd
import time
import random
from datetime import datetime
import math
import sys

sys.path.append("/app")
from src.storage.label_store import get_label_store

# --- Helper functions ---


def sanitize_float(val, default=0.0):
    """Convert value to float; replace NaN/Inf with default."""
    try:
        fval = float(val)
        if not math.isfinite(fval):
            return default
        return fval
    except (ValueError, TypeError):
        return default


def sanitize_int(val, default=0):
    """Convert value to int; replace NaN or missing with default."""
    try:
        if pd.isna(val):
            return default
        return int(val)
    except (ValueError, TypeError):
        return default


# --- Load test data ---

df = pd.read_csv("/app/data/processed/cs-training-temporal.csv")
test_df = df.sample(n=100, random_state=42)

prediction_ids = []

# --- Make predictions ---
for i, row in test_df.iterrows():
    payload = {
        "RevolvingUtilizationOfUnsecuredLines": sanitize_float(
            row["RevolvingUtilizationOfUnsecuredLines"]
        ),
        "age": sanitize_int(row["age"]),
        "NumberOfTime30_59DaysPastDueNotWorse": sanitize_int(
            row["NumberOfTime30_59DaysPastDueNotWorse"]
        ),
        "DebtRatio": sanitize_float(row["DebtRatio"]),
        "MonthlyIncome": sanitize_float(row["MonthlyIncome"]),
        "NumberOfOpenCreditLinesAndLoans": sanitize_int(row["NumberOfOpenCreditLinesAndLoans"]),
        "NumberOfTimes90DaysLate": sanitize_int(row["NumberOfTimes90DaysLate"]),
        "NumberRealEstateLoansOrLines": sanitize_int(row["NumberRealEstateLoansOrLines"]),
        "NumberOfTime60_89DaysPastDueNotWorse": sanitize_int(
            row["NumberOfTime60_89DaysPastDueNotWorse"]
        ),
        "NumberOfDependents": sanitize_int(row["NumberOfDependents"]),
    }

    # Send request to API
    try:
        response = requests.post("http://api:8000/predict", json=payload)
        if response.status_code == 200:
            # match label format used by label generator (e.g. pred_20251231_121613_839548)
            prediction_id = (
                f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(100000,999999)}"
            )
            pred_id = response.json().get("prediction_id")
            if pred_id is not None:
                prediction_ids.append((pred_id, sanitize_int(row["SeriousDlqin2yrs"])))
        else:
            print(f"⚠️ API returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Request failed: {e}")

    time.sleep(0.1)  # Small delay to simulate traffic

print(f"✅ Made {len(prediction_ids)} predictions")

# --- Simulate delayed labels (30% coverage) ---
label_store = get_label_store()
sample_size = int(0.8 * len(prediction_ids))  # Avoid crash if less than 30 predictions
for pred_id, true_label in random.sample(prediction_ids, k=sample_size):
    label_store.store_label(prediction_id=pred_id, true_label=true_label, label_source="simulation")

print(f"✅ Stored {sample_size} labels")
