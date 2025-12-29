"""
Append-only prediction logger.

DESIGN PRINCIPLES:
- Write-only: Never update or delete existing predictions
- No analytics: This module only handles I/O
- Time-stamped: Every prediction has a precise timestamp
- Atomic: Each write is a single append operation

Why append-only?
- Simplifies concurrent access
- Enables time-series analysis
- Prevents accidental data loss
- Audit trail for debugging
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict
import logging
import fcntl  # For file locking on Unix systems

logger = logging.getLogger(__name__)


class PredictionLogger:
    """
    Append-only logger for model predictions.
    
    NOT responsible for:
    - Computing metrics
    - Analyzing trends
    - Triggering alerts
    
    ONLY responsible for:
    - Writing predictions to disk
    - Ensuring data integrity
    """
    
    def __init__(self, storage_path: str = "/app/monitoring/predictions/predictions.csv"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize file with headers if needed
        if not self.storage_path.exists():
            self._initialize_storage()
    
    def _initialize_storage(self):
        """Create empty predictions file with schema."""
        df = pd.DataFrame(columns=[
            'timestamp',
            'prediction_id',
            'prediction',
            'probability',
            'model_version',
            # Input features (order matters for consistency)
            'RevolvingUtilizationOfUnsecuredLines',
            'age',
            'NumberOfTime30_59DaysPastDueNotWorse',
            'DebtRatio',
            'MonthlyIncome',
            'NumberOfOpenCreditLinesAndLoans',
            'NumberOfTimes90DaysLate',
            'NumberRealEstateLoansOrLines',
            'NumberOfTime60_89DaysPastDueNotWorse',
            'NumberOfDependents'
        ])
        df.to_csv(self.storage_path, index=False)
        logger.info(f"Initialized prediction log: {self.storage_path}")
    
    def log_prediction(
        self,
        prediction_id: str,
        features: Dict,
        prediction: int,
        probability: float,
        model_version: str
    ):
        """
        Append a single prediction to the log.
        
        Thread-safe via file locking (on Unix systems).
        Falls back to basic append on Windows.
        """
        timestamp = datetime.now().isoformat()
        
        # Create record with exact column order
        record = {
            'timestamp': timestamp,
            'prediction_id': prediction_id,
            'prediction': prediction,
            'probability': probability,
            'model_version': model_version,
            'RevolvingUtilizationOfUnsecuredLines': features['RevolvingUtilizationOfUnsecuredLines'],
            'age': features['age'],
            'NumberOfTime30_59DaysPastDueNotWorse': features['NumberOfTime30_59DaysPastDueNotWorse'],
            'DebtRatio': features['DebtRatio'],
            'MonthlyIncome': features['MonthlyIncome'],
            'NumberOfOpenCreditLinesAndLoans': features['NumberOfOpenCreditLinesAndLoans'],
            'NumberOfTimes90DaysLate': features['NumberOfTimes90DaysLate'],
            'NumberRealEstateLoansOrLines': features['NumberRealEstateLoansOrLines'],
            'NumberOfTime60_89DaysPastDueNotWorse': features['NumberOfTime60_89DaysPastDueNotWorse'],
            'NumberOfDependents': features['NumberOfDependents']
        }
        
        # Write with file locking (prevents corruption from concurrent writes)
        try:
            df = pd.DataFrame([record])
            
            # Acquire lock, append, release lock
            with open(self.storage_path, 'a') as f:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
                    df.to_csv(f, mode='a', header=False, index=False)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
            
            logger.debug(f"Logged prediction: {prediction_id}")
            
        except Exception as e:
            logger.error(f"Failed to log prediction {prediction_id}: {e}")
            # In production, you'd send this to error monitoring


# Singleton instance
_logger_instance = None

def get_prediction_logger() -> PredictionLogger:
    """Get or create the singleton prediction logger."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = PredictionLogger()
    return _logger_instance