from predict import predict
import json

with open("artifacts/schema.json") as f:
    features = json.load(f)["features"]

sample = {
    "RevolvingUtilizationOfUnsecuredLines": 0.5,
    "age": 45,
    "NumberOfTime30-59DaysPastDueNotWorse": 0,
    "DebtRatio": 0.3,
    "MonthlyIncome": 8000,
    "NumberOfOpenCreditLinesAndLoans": 10,
    "NumberOfTimes90DaysLate": 0,
    "NumberRealEstateLoansOrLines": 2,
    "NumberOfTime60-89DaysPastDueNotWorse": 0,
    "NumberOfDependents": 1
}

prob = predict(sample, features)
print("Prediction probability:", prob)
