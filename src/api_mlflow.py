"""
Production API with prediction logging for Phase 3 monitoring.

PHASE 3 RESPONSIBILITIES:
- Serve predictions from Production model
- Log predictions for monitoring
- THAT'S IT

NOT RESPONSIBLE FOR:
- Computing metrics (monitoring job does this)
- Detecting drift (monitoring job does this)
- Deciding if model should be retrained (Phase 4)
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import mlflow
import mlflow.sklearn
import numpy as np
import os
from datetime import datetime
from typing import Optional
import logging
import sys
from src.storage.prediction_logger import get_prediction_logger

# Add to path
sys.path.append("/app")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

MODEL_NAME = "credit-risk-model"
PRODUCTION_STAGE = "Production"

app = FastAPI(
    title="Credit Risk Prediction API (Phase 3)",
    description="Self-Healing MLOps Pipeline - Monitoring-Enabled API",
    version="3.0.0",
)

# Global state
model = None
model_version = None
model_uri = None
prediction_logger = None
_last_checked_version = None  # Track if we've checked for updates


def check_and_reload_model_if_needed():
    """
    Check if Production model has changed and reload if needed.

    This allows the API to pick up new models without restarting.
    Called before each prediction request.
    """
    global model, model_version, _last_checked_version

    try:
        client = mlflow.tracking.MlflowClient()
        versions = client.get_latest_versions(MODEL_NAME, stages=[PRODUCTION_STAGE])

        if not versions:
            logger.warning("No model in Production stage")
            return False

        latest_version = versions[0].version

        # Check if version changed
        if latest_version != _last_checked_version:
            logger.info(f"Production model updated: v{_last_checked_version} → v{latest_version}")
            load_production_model()
            _last_checked_version = latest_version
            logger.info(f"✅ Reloaded model to v{latest_version}")
            return True

        return False

    except Exception as e:
        logger.warning(f"Error checking for model updates: {e}")
        return False


class PredictionInput(BaseModel):
    """
    Input schema for predictions.

    Pydantic handles validation automatically.
    Invalid inputs are rejected before reaching our code.
    """

    RevolvingUtilizationOfUnsecuredLines: float
    age: int = Field(..., ge=18, le=120, description="Age must be 18-120")
    NumberOfTime30_59DaysPastDueNotWorse: int = Field(..., ge=0)
    DebtRatio: float
    MonthlyIncome: float = Field(..., ge=0, description="Monthly income must be positive")
    NumberOfOpenCreditLinesAndLoans: int = Field(..., ge=0)
    NumberOfTimes90DaysLate: int = Field(..., ge=0)
    NumberRealEstateLoansOrLines: int = Field(..., ge=0)
    NumberOfTime60_89DaysPastDueNotWorse: int = Field(..., ge=0)
    NumberOfDependents: int = Field(..., ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "RevolvingUtilizationOfUnsecuredLines": 0.766127,
                "age": 45,
                "NumberOfTime30_59DaysPastDueNotWorse": 2,
                "DebtRatio": 0.802982,
                "MonthlyIncome": 9120.0,
                "NumberOfOpenCreditLinesAndLoans": 13,
                "NumberOfTimes90DaysLate": 0,
                "NumberRealEstateLoansOrLines": 6,
                "NumberOfTime60_89DaysPastDueNotWorse": 0,
                "NumberOfDependents": 2,
            }
        }


class PredictionOutput(BaseModel):
    """
    Output schema for predictions.

    Phase 3: We return prediction + metadata.
    We do NOT return confidence scores (those imply calibration we haven't validated).
    """

    prediction: int = Field(..., description="0=no default risk, 1=default risk")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability of default")
    model_version: str = Field(..., description="Model version used for this prediction")
    prediction_id: str = Field(..., description="Unique ID for tracking this prediction")
    timestamp: str = Field(..., description="ISO timestamp of prediction")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    model_loaded: bool
    model_version: Optional[str]
    model_stage: str
    predictions_logged: int
    message: Optional[str] = None


def load_production_model():
    """
    Load Production model from MLflow Registry.

    Phase 2 contract: Only load Production models.
    If no Production model exists, API should not start.
    """
    global model, model_version, model_uri

    try:
        model_uri = f"models:/{MODEL_NAME}/{PRODUCTION_STAGE}"
        logger.info(f"Loading model: {model_uri}")
        model = mlflow.sklearn.load_model(model_uri)

        # Get version info
        client = mlflow.tracking.MlflowClient()
        versions = client.get_latest_versions(MODEL_NAME, stages=[PRODUCTION_STAGE])

        if not versions:
            raise ValueError(f"No model in {PRODUCTION_STAGE} stage")

        model_version = versions[0].version
        logger.info(f"✅ Loaded model version {model_version} from {PRODUCTION_STAGE}")

    except Exception as e:
        logger.error(f"❌ Failed to load Production model: {e}")
        raise RuntimeError(
            "Cannot start API: No model in Production stage. "
            "Train a model and promote it to Production first."
        )


@app.on_event("startup")
async def startup_event():
    """Initialize API on startup."""
    global prediction_logger, _last_checked_version

    logger.info("=" * 70)
    logger.info("API STARTING UP")
    logger.info("=" * 70)

    # Load model
    load_production_model()
    _last_checked_version = model_version  # Initialize tracking

    # Initialize prediction logger
    prediction_logger = get_prediction_logger()
    logger.info("✅ Prediction logger initialized")

    logger.info("=" * 70)
    logger.info("API READY")
    logger.info("=" * 70)


@app.get("/", response_model=dict)
async def root():
    """
    Root endpoint - basic health check.
    """
    return {
        "service": "Credit Risk Prediction API",
        "version": "3.0.0",
        "phase": "3 - Monitoring",
        "status": "healthy",
        "model_version": model_version,
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Detailed health check.

    Used by Docker health checks and load balancers.
    """
    # Count predictions (read from file)
    predictions_count = 0
    try:
        import pandas as pd
        from pathlib import Path

        pred_file = Path("/app/monitoring/predictions/predictions.csv")
        if pred_file.exists():
            df = pd.read_csv(pred_file)
            predictions_count = len(df)
    except Exception as e:
        logger.warning(f"Could not count predictions: {e}")

    is_healthy = model is not None

    return HealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        model_loaded=is_healthy,
        model_version=model_version,
        model_stage=PRODUCTION_STAGE,
        predictions_logged=predictions_count,
        message=None if is_healthy else "Model not loaded",
    )


@app.get("/model/info")
async def model_info():
    """
    Get current model information.

    Useful for debugging and monitoring which model is serving.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    client = mlflow.tracking.MlflowClient()
    versions = client.get_latest_versions(MODEL_NAME, stages=[PRODUCTION_STAGE])

    if versions:
        version_info = versions[0]
        return {
            "model_name": MODEL_NAME,
            "model_version": model_version,
            "model_stage": PRODUCTION_STAGE,
            "model_uri": model_uri,
            "run_id": version_info.run_id,
            "creation_timestamp": version_info.creation_timestamp,
            "last_updated_timestamp": version_info.last_updated_timestamp,
        }

    return {
        "model_name": MODEL_NAME,
        "model_version": model_version,
        "model_stage": PRODUCTION_STAGE,
    }


@app.post("/predict", response_model=PredictionOutput)
async def predict(input_data: PredictionInput):
    """
    Make prediction and log for monitoring.

    PHASE 3 BEHAVIOR:
    1. Check if Production model has been updated (reload if needed)
    2. Make prediction
    3. Log prediction (for monitoring job to analyze later)
    4. Return result

    We do NOT:
    - Compute metrics here
    - Check for drift here
    - Decide if model should be retrained

    Those are monitoring job responsibilities.
    """
    # Check if model has been updated and reload if needed
    check_and_reload_model_if_needed()

    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Prepare features (must match training order)
        features = np.array(
            [
                [
                    input_data.RevolvingUtilizationOfUnsecuredLines,
                    input_data.age,
                    input_data.NumberOfTime30_59DaysPastDueNotWorse,
                    input_data.DebtRatio,
                    input_data.MonthlyIncome,
                    input_data.NumberOfOpenCreditLinesAndLoans,
                    input_data.NumberOfTimes90DaysLate,
                    input_data.NumberRealEstateLoansOrLines,
                    input_data.NumberOfTime60_89DaysPastDueNotWorse,
                    input_data.NumberOfDependents,
                ]
            ]
        )

        # Predict
        prediction = int(model.predict(features)[0])
        probability = float(model.predict_proba(features)[0, 1])

        # Generate prediction ID
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        prediction_id = f"pred_{timestamp_str}"

        # Log prediction for monitoring
        # This is append-only, no analytics here
        if prediction_logger:
            try:
                prediction_logger.log_prediction(
                    prediction_id=prediction_id,
                    features=input_data.dict(),
                    prediction=prediction,
                    probability=probability,
                    model_version=str(model_version),
                )
            except Exception as e:
                # Logging failure should not break predictions
                # But we should know about it
                logger.error(f"Failed to log prediction {prediction_id}: {e}")

        # Return result
        return PredictionOutput(
            prediction=prediction,
            probability=probability,
            model_version=str(model_version),
            prediction_id=prediction_id,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/monitoring/stats")
async def monitoring_stats():
    """
    Get basic monitoring statistics.

    This is a convenience endpoint for quick checks.
    Real monitoring happens in the monitoring job.
    """
    try:
        import pandas as pd
        from pathlib import Path

        pred_file = Path("/app/monitoring/predictions/predictions.csv")

        if not pred_file.exists():
            return {"status": "no_predictions", "message": "No predictions logged yet"}

        df = pd.read_csv(pred_file)

        if len(df) == 0:
            return {"status": "no_predictions", "message": "Prediction log is empty"}

        # Basic stats
        recent_100 = df.tail(100)

        return {
            "total_predictions": len(df),
            "recent_100": {
                "count": len(recent_100),
                "positive_rate": float(recent_100["prediction"].mean()),
                "probability_mean": float(recent_100["probability"].mean()),
                "probability_std": float(recent_100["probability"].std()),
            },
            "note": "For detailed monitoring, see monitoring job results",
        }

    except Exception as e:
        logger.error(f"Failed to compute stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
