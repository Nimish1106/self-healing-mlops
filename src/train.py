import json
import joblib
from datetime import datetime , timezone
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss

from data import load_data
from preprocessing import split_features_target, build_preprocessing_pipeline

DATA_PATH = "data/cs-training.csv"
ARTIFACT_DIR = Path("artifacts")
ARTIFACT_DIR.mkdir(exist_ok=True)

def main():
    df = load_data(DATA_PATH)

    X, y = split_features_target(df, "SeriousDlqin2yrs")
    feature_names = X.columns.tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    preprocessor = build_preprocessing_pipeline(feature_names)
    X_train_p = preprocessor.fit_transform(X_train)
    X_test_p = preprocessor.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_p, y_train)

    probs = model.predict_proba(X_test_p)[:, 1]

    metrics = {
        "roc_auc": roc_auc_score(y_test, probs),
        "brier_score": brier_score_loss(y_test, probs),
    }

    # Save artifacts
    joblib.dump(model, ARTIFACT_DIR / "model.joblib")
    joblib.dump(preprocessor, ARTIFACT_DIR / "preprocessing.joblib")

    metadata = {
        "model_type": "RandomForestClassifier",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "features": feature_names,
    }

    with open(ARTIFACT_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    with open(ARTIFACT_DIR / "schema.json", "w") as f:
        json.dump({"features": feature_names}, f, indent=2)

    print("✅ Training complete")

if __name__ == "__main__":
    main()
