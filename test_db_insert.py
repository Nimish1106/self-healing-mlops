import sys

sys.path.append("/app")
from src.storage.repositories import MonitoringMetricsRepository
from datetime import datetime

try:
    repo = MonitoringMetricsRepository()
    record_id = repo.insert(
        timestamp=datetime.now(),
        lookback_hours=24,
        num_predictions=100,
        proxy_metrics={"positive_rate": 0.5},
        drift_summary={
            "dataset_drift_detected": False,
            "feature_drift_ratio": 0.2,
            "num_drifted_features": 2,
        },
        drift_summary_ref="test_ref",
    )
    print(f"✅ SUCCESS: Inserted record {record_id}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback

    traceback.print_exc()
