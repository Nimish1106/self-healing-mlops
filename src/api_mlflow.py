"""
Production API - Loads ONLY the Production model.
Logs predictions for future drift detection.
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

MODEL_NAME = "credit-risk-model"
PRODUCTION_STAGE = "Production"

app = FastAPI(
    title="Credit Risk Prediction API",
    description="Self-Healing MLOps Pipeline - Phase 2",
    version="2.0.0"
)

# Global state
model = None
model_version = None
model_uri = None


class PredictionInput(BaseModel):
    """Input schema."""
    RevolvingUtilizationOfUnsecuredLines: float
    age: int = Field(..., ge=18, le=120)
    NumberOfTime30_59DaysPastDueNotWorse: int = Field(..., ge=0)
    DebtRatio: float
    MonthlyIncome: float = Field(..., ge=0)
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
                "NumberOfDependents": 2
            }
        }


class PredictionOutput(BaseModel):
    """Output schema."""
    prediction: int
    probability: float
    model_version: str
    timestamp: str


def load_production_model():
    """
    Load ONLY the Production model from MLflow Registry.
    
    Phase 2 Rule: Simple and strict.
    No fallbacks, no guessing, no "latest".
    If no Production model exists, API should not start.
    """
    global model, model_version, model_uri
    
    try:
        # Get Production model
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
            f"Cannot start API: No model in Production stage. "
            f"Train a model and promote it to Production first."
        )


def log_prediction(input_data: dict, prediction: int, probability: float):
    """
    Log prediction for future drift detection.
    
    Phase 2: Minimal logging (just predictions).
    Phase 3: Will add drift detection on this data.
    """
    try:
        # Log to MLflow
        with mlflow.start_run(run_name=f"prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            mlflow.log_param("model_version", model_version)
            mlflow.log_metric("prediction", prediction)
            mlflow.log_metric("probability", probability)
            
            # Log input features as params (simplified)
            for key, value in input_data.items():
                mlflow.log_param(f"input_{key}", value)
    
    except Exception as e:
        # Don't fail predictions if logging fails
        logger.warning(f"Prediction logging failed: {e}")


@app.on_event("startup")
async def startup_event():
    """Load Production model on startup."""
    logger.info("🚀 Starting API...")
    load_production_model()
    logger.info("✨ API ready!")


@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "healthy",
        "service": "Credit Risk Prediction API",
        "model_version": model_version,
        "model_stage": PRODUCTION_STAGE
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy" if model is not None else "unhealthy",
        "model_loaded": model is not None,
        "model_version": model_version,
        "model_stage": PRODUCTION_STAGE,
        "mlflow_uri": MLFLOW_TRACKING_URI
    }


@app.get("/model/info")
async def model_info():
    """Get current model information."""
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
            "last_updated_timestamp": version_info.last_updated_timestamp
        }
    
    return {"model_version": model_version, "model_stage": PRODUCTION_STAGE}


@app.post("/predict", response_model=PredictionOutput)
async def predict(input_data: PredictionInput):
    """
    Make prediction using Production model.
    Logs prediction for future drift detection.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Prepare features
        features = np.array([[
            input_data.RevolvingUtilizationOfUnsecuredLines,
            input_data.age,
            input_data.NumberOfTime30_59DaysPastDueNotWorse,
            input_data.DebtRatio,
            input_data.MonthlyIncome,
            input_data.NumberOfOpenCreditLinesAndLoans,
            input_data.NumberOfTimes90DaysLate,
            input_data.NumberRealEstateLoansOrLines,
            input_data.NumberOfTime60_89DaysPastDueNotWorse,
            input_data.NumberOfDependents
        ]])
        
        # Predict
        prediction = int(model.predict(features)[0])
        probability = float(model.predict_proba(features)[0, 1])
        
        # Log prediction (async - don't block response)
        log_prediction(input_data.dict(), prediction, probability)
        
        return PredictionOutput(
            prediction=prediction,
            probability=probability,
            model_version=str(model_version),
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)