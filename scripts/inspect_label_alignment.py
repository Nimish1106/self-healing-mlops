import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append('/app')

import pandas as pd
from src.storage.prediction_logger import get_prediction_logger

pred_logger = get_prediction_logger()
preds = pred_logger.get_predictions_with_features()

print("preds columns:", preds.columns.tolist())
if 'prediction_id' in preds.columns:
    print("preds sample ids:", preds['prediction_id'].head().tolist())
else:
    print("preds sample rows:\n", preds.head().to_dict())

labels = pd.read_csv('/app/monitoring/labels/labels.csv')
print("labels count:", len(labels))
print("labels sample ids:", labels['prediction_id'].head().tolist())

if 'prediction_id' in preds.columns:
    common = set(preds['prediction_id']).intersection(set(labels['prediction_id']))
    print("common ids count:", len(common))
    print("example common ids:", list(common)[:5])
else:
    print("No 'prediction_id' column found in predictions_df")