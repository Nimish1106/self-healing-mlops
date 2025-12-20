from fastapi import FastAPI, HTTPException
from pydantic import BaseModel , Field
import json
from datetime import datetime , timezone

from predict import predict

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "predictions.log"


with open("artifacts/schema.json") as f:
    FEATURE_ORDER = json.load(f)["features"]

with open("artifacts/metadata.json") as f:
    METADATA = json.load(f)

app = FastAPI(title="Credit Risk API")

class InputData(BaseModel):
    RevolvingUtilizationOfUnsecuredLines: float 
    age: int
    NumberOfTime30_59DaysPastDueNotWorse: int = Field(
        ..., alias="NumberOfTime30-59DaysPastDueNotWorse"
    )
    DebtRatio: float
    MonthlyIncome: float
    NumberOfOpenCreditLinesAndLoans: int
    NumberOfTimes90DaysLate: int
    NumberRealEstateLoansOrLines: int
    NumberOfTime60_89DaysPastDueNotWorse: int = Field(
        ..., alias="NumberOfTime60-89DaysPastDueNotWorse"
    )
    NumberOfDependents: int

@app.get("/health")
def health():
    return {"status": "ok", "model": METADATA["model_type"]}

@app.post("/predict")
def predict_endpoint(data: InputData):
    try:
        prob = predict(data.model_dump(by_alias=True), FEATURE_ORDER)

        # simple logging (Phase 1 level)
        with open(LOG_FILE, "a") as f:
            f.write(
                f"{datetime.now(timezone.utc).isoformat()} | {prob} | {METADATA['model_type']}\n"
            )

        return {
            "prediction": prob,
            "model_version": METADATA["trained_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
