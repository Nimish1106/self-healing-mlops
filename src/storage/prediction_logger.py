"""
Prediction logger with FULL feature storage and header validation.

CRITICAL CHANGE: Must store raw features for replay-based evaluation.
CSV header validation ensures column consistency.

Why?
- Production and shadow models need to predict on SAME data
- Can't compare fairly if features are missing
- Enables true apples-to-apples comparison
- CSV header misalignment breaks downstream pipelines
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


def _get_expected_columns() -> list:
    """
    Get expected column order for predictions CSV.

    Returns:
        List of column names in canonical order
    """
    feature_columns = [
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

    return [
        "prediction_id",
        "timestamp",
        "model_version",
        "prediction",
        "probability",
        "application_date",
    ] + feature_columns


def _validate_csv_header(csv_path: Path) -> bool:
    """
    Validate CSV header matches expected column order.

    Args:
        csv_path: Path to CSV file

    Returns:
        True if header is valid, False otherwise
    """
    if not csv_path.exists():
        return True  # File doesn't exist yet, no header to validate

    try:
        df = pd.read_csv(csv_path, nrows=0)  # Read only header
        expected = _get_expected_columns()
        actual = list(df.columns)

        if actual == expected:
            return True

        logger.warning(
            f"CSV header mismatch!\n" f"  Expected: {expected}\n" f"  Actual:   {actual}"
        )
        return False

    except Exception as e:
        logger.error(f"Failed to validate CSV header: {e}")
        return False


def _repair_csv_header(csv_path: Path):
    """
    Repair CSV header by rewriting with correct order.

    If file exists and header is wrong, reinitialize with correct header.
    Existing data rows are discarded (this is acceptable for monitoring data).

    Args:
        csv_path: Path to CSV file
    """
    if not csv_path.exists():
        return  # Nothing to repair

    try:
        # Check header
        if _validate_csv_header(csv_path):
            return  # Header is already valid

        logger.warning(f"Repairing CSV header for {csv_path}...")

        # Reinitialize with correct header
        expected_columns = _get_expected_columns()
        df = pd.DataFrame(columns=expected_columns)
        df.to_csv(csv_path, index=False)

        logger.info(f"✅ CSV header repaired: {csv_path}")

    except PermissionError as e:
        logger.warning(
            f"⚠️  Cannot repair CSV header due to permission denied: {csv_path}. Data integrity may be affected until permissions are fixed. Error: {e}"
        )
        # Don't raise; just log warning to allow DAG to continue
    except Exception as e:
        logger.error(f"Failed to repair CSV header: {e}")
        raise


class PredictionLogger:
    """
    Log predictions WITH full feature vectors and CSV header validation.

    Schema:
    - prediction_id: Unique ID
    - timestamp: When prediction made
    - model_version: Model that made prediction
    - prediction: Predicted class (0/1)
    - probability: Predicted probability
    - application_date: Simulated timestamp (for temporal windows)
    - feature_1, feature_2, ..., feature_N: ALL input features

    CRITICAL: CSV header is validated/repaired on init.
    """

    def __init__(self, storage_path: str = "/app/monitoring/predictions/predictions.csv"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Feature columns (Give Me Some Credit dataset)
        self.feature_columns = [
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

        # Validate/repair existing CSV if present
        if self.storage_path.exists():
            is_valid = _validate_csv_header(self.storage_path)
            if not is_valid:
                logger.warning(f"⚠️  CSV header is misaligned. Repairing {self.storage_path}...")
                _repair_csv_header(self.storage_path)
        else:
            # Create new file with correct header
            self._initialize_storage()

    def _initialize_storage(self):
        """Create storage with feature columns in canonical order."""
        columns = _get_expected_columns()
        df = pd.DataFrame(columns=columns)
        df.to_csv(self.storage_path, index=False)
        logger.info(f"Initialized prediction storage: {self.storage_path}")

    def log_prediction(
        self,
        features: dict,
        prediction: int,
        probability: float,
        model_version: str,
        application_date: str = None,
        prediction_id: str = None,
    ) -> str:
        """
        Log prediction with FULL features in canonical column order.

        Args:
            features: Dictionary of feature values (all features required)
            prediction: Predicted class
            probability: Predicted probability
            model_version: Model identifier
            application_date: Simulated timestamp (optional)
            prediction_id: Unique ID (optional, auto-generated if not provided)

        Returns:
            prediction_id
        """
        # Allow caller (API) to supply a stable prediction_id; fall back to uuid4
        if prediction_id is None:
            prediction_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Validate all features present
        missing = set(self.feature_columns) - set(features.keys())
        if missing:
            raise ValueError(f"Missing features: {missing}")

        # Build record in CANONICAL column order
        record = {
            "prediction_id": prediction_id,
            "timestamp": timestamp,
            "model_version": model_version,
            "prediction": prediction,
            "probability": probability,
            "application_date": application_date or timestamp,
        }

        # Add all features
        for feat in self.feature_columns:
            record[feat] = features[feat]

        # Ensure DataFrame uses canonical column order
        df = pd.DataFrame([record])
        df = df[_get_expected_columns()]  # Reorder to canonical order

        # Append to CSV
        df.to_csv(self.storage_path, mode="a", header=False, index=False)

        return prediction_id

    def get_predictions_with_features(self, prediction_ids: list = None) -> pd.DataFrame:
        """
        Get predictions WITH features for replay evaluation.

        Args:
            prediction_ids: Optional list of specific IDs to retrieve

        Returns:
            DataFrame with predictions and features
        """
        if not self.storage_path.exists():
            return pd.DataFrame()

        df = pd.read_csv(self.storage_path)

        if prediction_ids is not None:
            df = df[df["prediction_id"].isin(prediction_ids)]

        logger.info(f"Retrieved {len(df)} predictions with features")
        return df

    def get_recent_predictions(
        self, days: int = 30, date_column: str = "application_date"
    ) -> pd.DataFrame:
        """
        Get recent predictions (temporal window).

        Args:
            days: Look back period
            date_column: Which date column to use

        Returns:
            DataFrame with recent predictions and features
        """
        if not self.storage_path.exists():
            return pd.DataFrame()

        df = pd.read_csv(self.storage_path)
        df[date_column] = pd.to_datetime(df[date_column])

        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        recent = df[df[date_column] >= cutoff].copy()

        logger.info(f"Retrieved {len(recent)} predictions from last {days} days")
        return recent


def _append_predictions(df, storage_path: str = "/app/monitoring/predictions/predictions.csv"):
    path = Path(storage_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    df.to_csv(path, mode="a", header=write_header, index=False)
    logger.info(f"Appended {len(df)} predictions to {path}")


# Singleton instance
_logger_instance = None


def get_prediction_logger() -> PredictionLogger:
    """Get or create singleton prediction logger."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = PredictionLogger()
    return _logger_instance
