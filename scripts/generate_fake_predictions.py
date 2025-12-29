import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import random

OUTPUT_PATH = Path("monitoring/predictions/predictions.csv")
NUM_ROWS = 300

np.random.seed(42)

rows = []
start_time = datetime.now() - timedelta(hours=6)

for i in range(NUM_ROWS):
    ts = start_time + timedelta(minutes=i)

    probability = np.clip(np.random.beta(2, 8), 0, 1)
    prediction = int(probability > 0.5)

    row = {
        "timestamp": ts.isoformat(),
        "prediction_id": f"fake_{i}",
        "prediction": prediction,
        "probability": probability,
        "model_version": "test",
        "RevolvingUtilizationOfUnsecuredLines": np.random.uniform(0, 1),
        "age": np.random.randint(21, 75),
        "NumberOfTime30_59DaysPastDueNotWorse": np.random.poisson(0.5),
        "DebtRatio": np.random.uniform(0, 1),
        "MonthlyIncome": np.random.randint(2000, 15000),
        "NumberOfOpenCreditLinesAndLoans": np.random.randint(1, 15),
        "NumberOfTimes90DaysLate": np.random.poisson(0.2),
        "NumberRealEstateLoansOrLines": np.random.randint(0, 5),
        "NumberOfTime60_89DaysPastDueNotWorse": np.random.poisson(0.3),
        "NumberOfDependents": np.random.randint(0, 4),
    }
    rows.append(row)

df = pd.DataFrame(rows)
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False)

print(f"✅ Generated {NUM_ROWS} fake predictions at {OUTPUT_PATH}")
