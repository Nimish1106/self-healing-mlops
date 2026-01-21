"""
Monitoring job: batch processor with PostgreSQL storage.

KEY CHANGES:
- Writes metrics to PostgreSQL (queryable)
- Stores artifacts as files (immutable)
- NO label tracking (async concern, belongs in decisions)
- Uses feature_drift_ratio (not drift_share)
"""
from typing import Dict
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import logging
import sys

sys.path.append('/app')
from src.analytics.proxy_metrics import analyze_proxy_metrics
from src.analytics.drift_detection import DriftDetector, load_reference_data
from src.storage.repositories import MonitoringMetricsRepository  # ✅ NEW
from scripts.bootstrap_reference import verify_reference_integrity

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Statistical validity threshold
MIN_SAMPLES_FOR_ANALYSIS = 200

# Feature columns for drift detection
FEATURE_COLUMNS = [
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
]

NUMERICAL_FEATURES = [
    'RevolvingUtilizationOfUnsecuredLines',
    'age',
    'NumberOfTime30_59DaysPastDueNotWorse',
    'DebtRatio',
    'MonthlyIncome',
    'NumberOfOpenCreditLinesAndLoans',
    'NumberOfTimes90DaysLate',
    'NumberRealEstateLoansOrLines',
    'NumberOfTime60_89DaysPastDueNotWorse',
    'NumberOfDependents',
]

CATEGORICAL_FEATURES = []  # No categorical features in this dataset


class MonitoringJob:
    """
    Batch job that runs monitoring analytics.
    
    ✅ NEW: Writes to PostgreSQL + file artifacts
    ❌ REMOVED: Label tracking (async, belongs in decision time)
    """
    
    def __init__(
        self,
        predictions_path: str = "/app/monitoring/predictions/predictions.csv",
        reference_dir: str = "/app/monitoring/reference",
        output_dir: str = "/app/monitoring/metrics/monitoring_results"
    ):
        self.predictions_path = Path(predictions_path)
        self.reference_dir = reference_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # ✅ NEW: Database repository
        self.metrics_repo = MonitoringMetricsRepository()
        
        # Verify reference integrity at startup
        logger.info("Verifying reference data integrity...")
        verify_reference_integrity(reference_dir)
        
        # Load frozen reference
        self.reference_data, self.reference_metadata = load_reference_data(reference_dir)
        logger.info("Monitoring job initialized with database storage")
    
    def load_predictions(self, lookback_hours: int = 24) -> pd.DataFrame:
        """Load recent predictions."""
        if not self.predictions_path.exists():
            logger.warning(f"No predictions file at {self.predictions_path}")
            return pd.DataFrame()
        
        df = pd.read_csv(self.predictions_path)
        
        if len(df) == 0:
            return df
        
        # Filter to time window
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff = pd.Timestamp.now() - pd.Timedelta(hours=lookback_hours)
        df_recent = df[df['timestamp'] > cutoff]
        
        logger.info(f"Loaded {len(df_recent)} predictions from last {lookback_hours}h")
        return df_recent
    
    def run(self, lookback_hours: int = 24) -> Dict:
        """
        Execute one monitoring cycle.
        
        ✅ NEW: Writes to database + saves artifacts
        """
        logger.info("=" * 70)
        logger.info(f"MONITORING JOB STARTED - Lookback: {lookback_hours}h")
        logger.info("=" * 70)
        
        run_timestamp = datetime.now()
        
        # Load data
        predictions = self.load_predictions(lookback_hours)
        
        # Enforce minimum sample size
        if len(predictions) < MIN_SAMPLES_FOR_ANALYSIS:
            logger.warning(
                f"Insufficient samples for statistical analysis: "
                f"{len(predictions)} < {MIN_SAMPLES_FOR_ANALYSIS}. "
                f"Skipping analytics until more data accumulates."
            )
            return {
                "status": "insufficient_data",
                "num_predictions": len(predictions),
                "min_required": MIN_SAMPLES_FOR_ANALYSIS,
                "message": "Waiting for more predictions to enable analysis"
            }
        
        # Analysis window metadata
        analysis_window = {
            "lookback_hours": lookback_hours,
            "start_time": predictions['timestamp'].min().isoformat(),
            "end_time": predictions['timestamp'].max().isoformat(),
            "num_predictions": len(predictions)
        }
        
        results = {
            "timestamp": run_timestamp.isoformat(),
            "analysis_window": analysis_window
        }
        
        # 1. PROXY METRICS
        logger.info("\n--- Computing Proxy Metrics ---")
        try:
            proxy_results = analyze_proxy_metrics(predictions)
            results['proxy_metrics'] = proxy_results
            logger.info("✅ Proxy metrics computed")
        except Exception as e:
            logger.error(f"Proxy metrics failed: {e}")
            results['proxy_metrics'] = {"status": "error", "error": str(e)}
        
        # 2. DRIFT DETECTION
        logger.info("\n--- Running Drift Detection ---")
        try:
            drift_detector = DriftDetector(
                reference_data=self.reference_data,
                feature_columns=FEATURE_COLUMNS,
                numerical_features=NUMERICAL_FEATURES,
                categorical_features=CATEGORICAL_FEATURES,
                reference_metadata=self.reference_metadata
            )
            
            drift_results = drift_detector.detect_drift(predictions)
            
            # Extract drift summary
            drift_summary_timestamp = drift_results.get('timestamp', 'unknown')
            drift_summary_filename = f"drift_summary_{drift_summary_timestamp.replace(':', '-').split('.')[0]}.json"
            
            # ✅ RENAMED: drift_share → feature_drift_ratio
            drift_summary = {
                "dataset_drift_detected": drift_results.get('dataset_drift_detected', False),
                "feature_drift_ratio": drift_results.get('drift_share', 0.0),  # ✅ RENAMED
                "num_drifted_features": drift_results.get('num_drifted_features', 0),
                "num_features_evaluated": drift_results.get('num_features_evaluated', len(FEATURE_COLUMNS)),
                "num_features_excluded": drift_results.get('num_features_excluded', 0),
                "drifted_features": drift_results.get('features', [])  # Full feature details
            }
            
            # Save drift artifacts (files, not database)
            drift_summary_ref = self._save_drift_artifacts(drift_results, run_timestamp)
            
            # Minimal drift reference for database
            results['drift_detection'] = {
                "drift_summary_ref": drift_summary_ref,
                "dataset_drift_detected": drift_summary["dataset_drift_detected"],
                "feature_drift_ratio": drift_summary["feature_drift_ratio"],  # ✅ RENAMED
                "num_drifted_features": drift_summary["num_drifted_features"],
                "num_features_evaluated": drift_summary["num_features_evaluated"],
                "num_features_excluded": drift_summary["num_features_excluded"]
            }
            
            # Log drift as neutral observation
            logger.info(
                f"Drift summary: {drift_summary['num_drifted_features']}/{drift_summary['num_features_evaluated']} features "
                f"flagged (feature_drift_ratio={drift_summary['feature_drift_ratio']:.2%}). "
                f"Reference: {drift_summary_ref}"
            )
            
        except Exception as e:
            logger.error(f"Drift detection failed: {e}")
            results['drift_detection'] = {"status": "error", "error": str(e)}
            drift_summary = {}
            drift_summary_ref = None
        
        # ✅ NEW: Write to database
        try:
            self._write_to_database(
                timestamp=run_timestamp,
                lookback_hours=lookback_hours,
                num_predictions=len(predictions),
                proxy_metrics=results.get('proxy_metrics', {}),
                drift_summary=drift_summary,
                drift_summary_ref=drift_summary_ref
            )
        except Exception as e:
            logger.error(f"Database write failed: {e}")
            logger.exception("Full traceback:")
        
        # ✅ JSON file saving DISABLED - all metrics now in database
        # self._save_results(results)
        
        # Prune old HTML reports
        self._prune_html_reports(max_keep=50)
        
        logger.info("\n" + "=" * 70)
        logger.info("MONITORING JOB COMPLETE")
        logger.info("=" * 70)
        
        return results
    
    def _save_drift_artifacts(self, drift_results: Dict, timestamp: datetime) -> str:
        """
        Return drift summary reference (JSON saving DISABLED).
        
        ✅ All drift metrics stored in database
        ✅ HTML reports kept for visualization only
        
        Returns:
            Reference identifier
        """
        timestamp_str = timestamp.strftime("%Y-%m-%dT%H-%M-%S")
        
        # ✅ JSON saving DISABLED - all data in database now
        # summaries_dir = Path("/app/monitoring/drift/summaries")
        # summaries_dir.mkdir(parents=True, exist_ok=True)
        # summary_filename = f"drift_summary_{timestamp_str}.json"
        # summary_path = summaries_dir / summary_filename
        # with open(summary_path, 'w') as f:
        #     json.dump(drift_results, f, indent=2)
        
        # Return reference for database
        return f"drift_summary_{timestamp_str}"
    
    def _write_to_database(
        self,
        timestamp: datetime,
        lookback_hours: int,
        num_predictions: int,
        proxy_metrics: Dict,
        drift_summary: Dict,
        drift_summary_ref: str
    ):
        """
        Write metrics to PostgreSQL.
        
        ✅ CRITICAL: Only metrics, NOT labels (async concern)
        """
        logger.info("Writing metrics to database...")
        
        # Extract overall stats from proxy metrics
        overall_stats = proxy_metrics.get('overall_stats', {})
        
        record_id = self.metrics_repo.insert(
            timestamp=timestamp,
            lookback_hours=lookback_hours,
            num_predictions=num_predictions,
            proxy_metrics={
                'positive_rate': overall_stats.get('positive_rate'),
                'probability_mean': overall_stats.get('probability_mean'),
                'probability_std': overall_stats.get('probability_std'),
                'entropy': proxy_metrics.get('entropy')  # ✅ FIXED: Top-level, not in overall_stats
            },
            drift_summary={
                'dataset_drift_detected': drift_summary.get('dataset_drift_detected', False),
                'feature_drift_ratio': drift_summary.get('feature_drift_ratio', 0.0),  # ✅ RENAMED
                'num_drifted_features': drift_summary.get('num_drifted_features', 0)
            },
            drift_summary_ref=drift_summary_ref
        )
        
        logger.info(f"✅ Metrics written to database: {record_id}")
    
    def _save_results(self, results: Dict):
        """Save monitoring results as JSON (legacy)."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"monitoring_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved: {output_file}")
    
    def _prune_html_reports(self, max_keep: int = 50):
        """Prune old HTML drift reports."""
        try:
            reports_dir = Path('/app/monitoring/reports/drift_reports')
            if not reports_dir.exists():
                return
            
            html_files = sorted(
                reports_dir.glob('drift_report_*.html'),
                reverse=True
            )
            
            if len(html_files) <= max_keep:
                return
            
            files_to_delete = html_files[max_keep:]
            for filepath in files_to_delete:
                try:
                    filepath.unlink()
                    logger.debug(f"Pruned old report: {filepath.name}")
                except Exception as e:
                    logger.warning(f"Could not delete {filepath}: {e}")
            
            logger.info(
                f"HTML report pruning: kept {len(html_files[:max_keep])}/{len(html_files)}, "
                f"deleted {len(files_to_delete)} old reports"
            )
        
        except Exception as e:
            logger.warning(f"HTML report pruning failed (non-critical): {e}")


def run_monitoring_job(lookback_hours: int = 24):
    """Convenience function to run monitoring job."""
    job = MonitoringJob()
    return job.run(lookback_hours)


if __name__ == "__main__":
    run_monitoring_job()