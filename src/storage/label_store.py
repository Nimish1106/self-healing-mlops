"""
Label store with IDEMPOTENT label updates.

CRITICAL CHANGE: One label per prediction_id (no duplicates).

Why?
- Duplicate labels corrupt evaluation metrics
- Makes gate decisions meaningless
- Reflects real-world label systems
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class LabelStore:
    """
    Store ground truth labels with idempotency guarantee.
    
    ENFORCED: One label per prediction_id.
    If label exists → update, don't duplicate.
    """
    
    def __init__(self, storage_path: str = "/app/monitoring/labels/labels.csv"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.storage_path.exists():
            self._initialize_storage()
    
    def _initialize_storage(self):
        """Create empty labels file."""
        df = pd.DataFrame(columns=[
            'prediction_id',
            'true_label',
            'label_timestamp',
            'label_source',
            'days_delayed',
            'updated_at'  # Track last update
        ])
        df.to_csv(self.storage_path, index=False)
        logger.info(f"Initialized label store: {self.storage_path}")
    
    def store_label(
        self,
        prediction_id: str,
        true_label: int,
        label_source: str = "manual",
        prediction_timestamp: Optional[str] = None
    ):
        """
        Store label with idempotency.
        
        If prediction_id already has label:
        - Update existing record
        - Log warning
        
        Args:
            prediction_id: ID of prediction
            true_label: Ground truth (0 or 1)
            label_source: Where label came from
            prediction_timestamp: Original prediction time
        """
        label_timestamp = datetime.now().isoformat()
        
        # Calculate delay
        days_delayed = None
        if prediction_timestamp:
            try:
                pred_time = pd.to_datetime(prediction_timestamp)
                label_time = pd.to_datetime(label_timestamp)
                days_delayed = (label_time - pred_time).days
            except Exception as e:
                logger.warning(f"Could not calculate delay: {e}")
        
        # Load existing labels
        if self.storage_path.exists():
            df = pd.read_csv(self.storage_path)
        else:
            df = pd.DataFrame()
        
        # Check if label already exists
        existing_mask = df['prediction_id'] == prediction_id
        
        if existing_mask.any():
            # Update existing
            old_label = df.loc[existing_mask, 'true_label'].values[0]
            
            if old_label != true_label:
                logger.warning(
                    f"⚠️ Label conflict for {prediction_id}: "
                    f"old={old_label}, new={true_label}. Updating."
                )
            
            df.loc[existing_mask, 'true_label'] = true_label
            df.loc[existing_mask, 'label_timestamp'] = label_timestamp
            df.loc[existing_mask, 'label_source'] = label_source
            df.loc[existing_mask, 'days_delayed'] = days_delayed
            df.loc[existing_mask, 'updated_at'] = label_timestamp
            
            logger.info(f"Updated label for {prediction_id}: {true_label}")
        else:
            # Insert new
            new_record = pd.DataFrame([{
                'prediction_id': prediction_id,
                'true_label': true_label,
                'label_timestamp': label_timestamp,
                'label_source': label_source,
                'days_delayed': days_delayed,
                'updated_at': label_timestamp
            }])
            
            df = pd.concat([df, new_record], ignore_index=True)
            
            logger.info(f"Stored new label for {prediction_id}: {true_label}")
        
        # Save
        df.to_csv(self.storage_path, index=False)
    
    def get_labeled_predictions(
        self,
        predictions_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Join predictions with labels (inner join).
        
        Returns only predictions that have labels.
        
        Args:
            predictions_df: DataFrame with predictions
            
        Returns:
            DataFrame with predictions + labels
        """
        if not self.storage_path.exists():
            return pd.DataFrame()
        
        labels_df = pd.read_csv(self.storage_path)
        
        if len(labels_df) == 0:
            return pd.DataFrame()
        
        # Validate no duplicates
        duplicate_count = labels_df['prediction_id'].duplicated().sum()
        if duplicate_count > 0:
            logger.error(
                f"🚨 CORRUPT LABEL STORE: {duplicate_count} duplicate prediction_ids found!"
            )
            # Deduplicate (keep last)
            labels_df = labels_df.drop_duplicates(subset='prediction_id', keep='last')
        
        # Join
        merged = predictions_df.merge(
            labels_df[['prediction_id', 'true_label', 'days_delayed']],
            on='prediction_id',
            how='inner'
        )
        
        logger.info(f"Found {len(merged)} predictions with labels")
        return merged
    
    def get_label_coverage(
        self,
        predictions_df: pd.DataFrame
    ) -> Dict:
        """
        Calculate label coverage statistics.
        
        Returns:
            Dictionary with coverage metrics
        """
        labeled = self.get_labeled_predictions(predictions_df)
        
        total = len(predictions_df)
        labeled_count = len(labeled)
        
        return {
            'total_predictions': total,
            'labeled_predictions': labeled_count,
            'coverage_rate': labeled_count / total if total > 0 else 0.0,
            'unlabeled_predictions': total - labeled_count
        }


# Singleton
_label_store_instance = None

def get_label_store() -> LabelStore:
    """Get or create singleton label store."""
    global _label_store_instance
    if _label_store_instance is None:
        _label_store_instance = LabelStore()
    return _label_store_instance