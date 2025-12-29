"""
Drift detection using Evidently AI.

CRITICAL FRAMING:
Evidently tells us IF distributions changed.
Evidently does NOT tell us:
- Whether change is bad
- Whether we should retrain
- Whether accuracy degraded (we don't have labels)

DRIFT ≠ MODEL FAILURE
Drift means: "The data distribution looks different from reference."

Possible interpretations:
1. World changed → Model might be outdated (common interpretation)
2. Data quality issue → Fix pipeline, not model
3. Expected seasonality → No action needed
4. New market segment → Model working correctly on new data

The decision "what to do about drift" belongs in Phase 4, not here.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json
import logging

from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
from evidently.metrics import DatasetDriftMetric, ColumnDriftMetric

logger = logging.getLogger(__name__)


class DriftDetector:
    """
    Wrapper around Evidently AI for drift detection.
    
    DESIGN: Keep Evidently at arm's length.
    We call it, extract results, return structured data.
    We don't let Evidently's opinions dictate our architecture.
    """
    
    def __init__(
        self,
        reference_data: pd.DataFrame,
        feature_columns: List[str],
        reference_metadata: Optional[Dict] = None
    ):
        """
        Initialize with FROZEN reference data.
        
        Args:
            reference_data: Immutable reference distribution
            feature_columns: Features to monitor
            reference_metadata: Optional metadata about reference
        """
        self.reference_data = reference_data[feature_columns].copy()
        self.feature_columns = feature_columns
        self.reference_metadata = reference_metadata or {}
        
        logger.info(f"DriftDetector initialized:")
        logger.info(f"  Reference samples: {len(self.reference_data)}")
        logger.info(f"  Features monitored: {len(self.feature_columns)}")
        
        if self.reference_metadata:
            logger.info(f"  Reference created: {self.reference_metadata.get('created_at', 'unknown')}")
    
    def detect_drift(
        self,
        current_data: pd.DataFrame,
        save_report: bool = True,
        report_dir: str = "/app/monitoring/reports/drift_reports"
    ) -> Dict:
        """
        Run drift detection.
        
        Returns statistical test results, NOT action recommendations.
        
        Evidently uses various statistical tests:
        - Kolmogorov-Smirnov (KS) for continuous features
        - Chi-squared for categorical features
        - Other tests depending on data type
        
        We return:
        - Test statistics
        - P-values
        - Which features drifted (by statistical test)
        
        We do NOT return:
        - "Should retrain" (that's Phase 4)
        - "Drift is bad" (that's domain-specific)
        - Action recommendations (not our job)
        """
        if len(current_data) == 0:
            logger.warning("No current data provided")
            return {"status": "no_data"}
        
        # Extract features
        current_features = current_data[self.feature_columns].copy()
        
        logger.info(f"Running drift detection on {len(current_features)} samples")
        
        # Create Evidently report
        report = Report(metrics=[
            DataDriftPreset(),
            DatasetDriftMetric()
        ])
        
        # Run analysis
        try:
            report.run(
                reference_data=self.reference_data,
                current_data=current_features
            )
        except Exception as e:
            logger.error(f"Evidently drift detection failed: {e}")
            return {"status": "error", "error": str(e)}
        
        # Extract results
        results_dict = report.as_dict()
        drift_summary = self._parse_evidently_results(results_dict)
        
        # Save report if requested
        if save_report:
            self._save_outputs(report, drift_summary, report_dir)
        
        return drift_summary
    
    def _parse_evidently_results(self, results: Dict) -> Dict:
        """
        Extract structured data from Evidently output.
        
        Evidently returns complex nested dictionaries.
        We flatten to a simpler structure for downstream use.
        """
        try:
            # Find dataset drift metric
            dataset_drift_result = None
            for metric in results.get('metrics', []):
                if metric.get('metric') == 'DatasetDriftMetric':
                    dataset_drift_result = metric.get('result', {})
                    break
            
            if not dataset_drift_result:
                return {"status": "parse_error", "message": "Could not find DatasetDriftMetric"}
            
            # Extract summary
            drift_summary = {
                "timestamp": datetime.now().isoformat(),
                "reference_metadata": self.reference_metadata,
                
                # Dataset-level statistics
                "dataset_drift_detected": dataset_drift_result.get('dataset_drift', False),
                "drift_share": dataset_drift_result.get('drift_share', 0.0),  # Fraction of features drifted
                "num_drifted_features": dataset_drift_result.get('number_of_drifted_columns', 0),
                "num_features_total": len(self.feature_columns),
                
                # Per-feature details
                "feature_drift_details": []
            }
            
            # Extract per-feature drift info
            drift_by_column = dataset_drift_result.get('drift_by_columns', {})
            for feature, drift_info in drift_by_column.items():
                drift_summary['feature_drift_details'].append({
                    "feature": feature,
                    "drift_detected": drift_info.get('drift_detected', False),
                    "drift_score": drift_info.get('drift_score'),
                    "stat_test": drift_info.get('stattest_name', 'unknown'),
                    "threshold": drift_info.get('stattest_threshold'),
                    # Include current vs reference stats
                    "current_distribution": drift_info.get('current', {}),
                    "reference_distribution": drift_info.get('reference', {})
                })
            
            logger.info(f"Drift detection results:")
            logger.info(f"  Dataset drift: {drift_summary['dataset_drift_detected']}")
            logger.info(f"  Drift share: {drift_summary['drift_share']:.2%}")
            logger.info(f"  Drifted features: {drift_summary['num_drifted_features']}/{drift_summary['num_features_total']}")
            
            return drift_summary
            
        except Exception as e:
            logger.error(f"Error parsing Evidently results: {e}")
            return {"status": "parse_error", "error": str(e)}
    
    def _save_outputs(self, report: Report, summary: Dict, report_dir: str):
        """Save Evidently HTML report and JSON summary."""
        report_path = Path(report_dir)
        report_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save HTML (for human review)
        html_file = report_path / f"drift_report_{timestamp}.html"
        report.save_html(str(html_file))
        logger.info(f"Saved HTML report: {html_file}")
        
        # Save JSON (for programmatic access)
        json_file = report_path / f"drift_summary_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Saved JSON summary: {json_file}")


def load_reference_data(reference_dir: str = "/app/monitoring/reference") -> tuple:
    """
    Load frozen reference data.
    
    Returns:
        (reference_df, metadata_dict)
    
    Raises if reference doesn't exist (must bootstrap first).
    """
    reference_file = Path(reference_dir) / "reference_data.csv"
    metadata_file = Path(reference_dir) / "reference_metadata.json"
    
    if not reference_file.exists():
        raise FileNotFoundError(
            f"Reference data not found at {reference_file}. "
            f"Run 'python scripts/bootstrap_reference.py' first."
        )
    
    df = pd.read_csv(reference_file)
    
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
    
    logger.info(f"Loaded reference data: {len(df)} samples")
    return df, metadata