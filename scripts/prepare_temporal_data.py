"""
Add simulated timestamps to dataset for temporal windows.
Run ONCE before training.
"""
import pandas as pd
import sys

sys.path.append("/app")
from src.utils.temporal_utils import TemporalWindows

# Load raw data
df = pd.read_csv("/app/data/raw/cs-training.csv")

# Add timestamps
temporal = TemporalWindows()
df_temporal = temporal.add_simulated_timestamps(
    df,
    start_date="2022-01-01",
    end_date="2026-01-01",
    date_column="application_date",
    random_seed=42,  # Reproducible
)

# Save
df_temporal.to_csv("/app/data/processed/cs-training-temporal.csv", index=False)
print(f"✅ Temporal data created: {len(df_temporal)} rows")
