import joblib
import numpy as np
import pandas as pd

ARTIFACT_DIR = "artifacts"

model = joblib.load(f"{ARTIFACT_DIR}/model.joblib")
preprocessor = joblib.load(f"{ARTIFACT_DIR}/preprocessing.joblib")

def predict(features: dict, feature_order: list):
    x = pd.DataFrame([[features[f] for f in feature_order]], columns=feature_order)
    x_p = preprocessor.transform(x)
    prob = model.predict_proba(x_p)[0, 1]
    return float(prob)
