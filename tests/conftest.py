"""
Pytest configuration and shared fixtures.

Fixtures provide reusable test data and setup.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def sample_predictions_df():
    """Sample predictions DataFrame for testing."""
    np.random.seed(42)
    n_samples = 300

    data = {
        "timestamp": pd.date_range("2024-01-01", periods=n_samples, freq="1H"),
        "prediction_id": [f"pred_{i}" for i in range(n_samples)],
        "prediction": np.random.binomial(1, 0.1, n_samples),
        "probability": np.random.beta(2, 8, n_samples),
        "model_version": ["1"] * n_samples,
        # Features
        "RevolvingUtilizationOfUnsecuredLines": np.random.uniform(0, 1, n_samples),
        "age": np.random.randint(18, 80, n_samples),
        "NumberOfTime30_59DaysPastDueNotWorse": np.random.randint(0, 5, n_samples),
        "DebtRatio": np.random.uniform(0, 2, n_samples),
        "MonthlyIncome": np.random.uniform(1000, 15000, n_samples),
        "NumberOfOpenCreditLinesAndLoans": np.random.randint(0, 20, n_samples),
        "NumberOfTimes90DaysLate": np.random.randint(0, 3, n_samples),
        "NumberRealEstateLoansOrLines": np.random.randint(0, 10, n_samples),
        "NumberOfTime60_89DaysPastDueNotWorse": np.random.randint(0, 3, n_samples),
        "NumberOfDependents": np.random.randint(0, 5, n_samples),
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_labels_df(sample_predictions_df):
    """Sample labels DataFrame for testing."""
    # Create labels for first 200 predictions
    prediction_ids = sample_predictions_df["prediction_id"].iloc[:200].tolist()

    data = {
        "prediction_id": prediction_ids,
        "true_label": np.random.binomial(1, 0.1, len(prediction_ids)),
        "label_timestamp": pd.date_range("2024-01-02", periods=len(prediction_ids), freq="1H"),
        "label_source": "test",
        "days_delayed": np.random.randint(1, 30, len(prediction_ids)),
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_reference_data():
    """Sample reference data for drift detection."""
    np.random.seed(42)
    n_samples = 200

    data = {
        "RevolvingUtilizationOfUnsecuredLines": np.random.uniform(0, 1, n_samples),
        "age": np.random.randint(18, 80, n_samples),
        "NumberOfTime30_59DaysPastDueNotWorse": np.random.randint(0, 5, n_samples),
        "DebtRatio": np.random.uniform(0, 2, n_samples),
        "MonthlyIncome": np.random.uniform(1000, 15000, n_samples),
        "NumberOfOpenCreditLinesAndLoans": np.random.randint(0, 20, n_samples),
        "NumberOfTimes90DaysLate": np.random.randint(0, 3, n_samples),
        "NumberRealEstateLoansOrLines": np.random.randint(0, 10, n_samples),
        "NumberOfTime60_89DaysPastDueNotWorse": np.random.randint(0, 3, n_samples),
        "NumberOfDependents": np.random.randint(0, 5, n_samples),
        "SeriousDlqin2yrs": np.random.binomial(1, 0.1, n_samples),
    }

    return pd.DataFrame(data)


@pytest.fixture
def temp_monitoring_dir():
    """Temporary directory for monitoring outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def feature_columns():
    """Standard feature column names."""
    return [
        "RevolvingUtilizationOfUnsecuredLines",
        "age",
        "NumberOfTime30_59DaysPastDueNotWorse",
        "DebtRatio",
        "MonthlyIncome",
        "NumberOfOpenCreditLinesAndLoans",
        "NumberOfTimes90DaysLate",
        "NumberRealEstateLoansOrLines",
        "NumberOfTime60_89DaysPastDueNotWorse",
        "NumberOfDependents",
    ]
