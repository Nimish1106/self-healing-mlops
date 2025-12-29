"""
Monitoring job: batch processor that calls analytics modules.
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
from scripts.bootstrap_reference import verify_reference_integrity

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Statistical validity threshold
# Why 200? 
# - Sufficient for CLT to apply
# - Provides power for drift tests (KS, Chi-sq)
# - Conservative enough to avoid false positives
# - Small enough to be practical (< 1 day at moderate traffic)
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


class MonitoringJob:
    """
    Batch job that runs monitoring analytics.
    
    Design: Pure data processing, no decision-making.
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
        
        # CORRECTION 5: Verify reference integrity at startup
        # If reference is corrupted, all downstream analysis is garbage
        # Better to fail fast than silently produce wrong results
        logger.info("Verifying reference data integrity...")
        verify_reference_integrity(reference_dir)
        
        # Load frozen reference
        self.reference_data, self.reference_metadata = load_reference_data(reference_dir)
        logger.info("Monitoring job initialized")
    
    def load_predictions(self, lookback_hours: int = 24) -> pd.DataFrame:
        """
        Load recent predictions.
        
        Args:
            lookback_hours: How far back to load data
        """
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
        
        Returns monitoring results (does NOT act on them).
        """
        logger.info("=" * 70)
        logger.info(f"MONITORING JOB STARTED - Lookback: {lookback_hours}h")
        logger.info("=" * 70)
        
        # Load data
        predictions = self.load_predictions(lookback_hours)
        
        # CORRECTION 1: Enforce minimum sample size for statistical validity
        # Running drift tests on 50 samples is mathematically dishonest
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
        
        # CORRECTION 4: Add explicit time-window metadata
        # Time context is critical for interpreting drift
        analysis_window = {
            "lookback_hours": lookback_hours,
            "start_time": predictions['timestamp'].min().isoformat(),
            "end_time": predictions['timestamp'].max().isoformat(),
            "num_predictions": len(predictions)
        }
        
        results = {
            "timestamp": datetime.now().isoformat(),
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
                reference_metadata=self.reference_metadata
            )
            
            drift_results = drift_detector.detect_drift(predictions)
            results['drift_detection'] = drift_results
            
            # CORRECTION 2 & 3: Report drift as neutral observation, not warning
            # Drift is a statistical signal, not a failure condition
            # Phase 3 observes and reports; it does NOT judge or act
            num_drifted = drift_results.get('num_drifted_features', 0)
            drift_share = drift_results.get('drift_share', 0.0)
            
            logger.info(
                f"Drift summary: {num_drifted}/{len(FEATURE_COLUMNS)} features "
                f"flagged by statistical tests (drift_share={drift_share:.2%}). "
                f"No action taken (observation only)."
            )
            
        except Exception as e:
            logger.error(f"Drift detection failed: {e}")
            results['drift_detection'] = {"status": "error", "error": str(e)}
        
        # 3. SAVE RESULTS
        self._save_results(results)
        
        # # 4. LOG TO MLFLOW (optional)
        # self._log_to_mlflow(results)
        
        # logger.info("\n" + "=" * 70)
        # logger.info("MONITORING JOB COMPLETE")
        # logger.info("=" * 70)
        
        return results
    
    def _save_results(self, results: Dict):
        """Save monitoring results as JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"monitoring_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved: {output_file}")
    
    # def _log_to_mlflow(self, results: Dict):
    #     """
    #     Log monitoring results to MLflow.
        
    #     CORRECTION 6: Honest framing of what MLflow provides here.
    #     This provides lightweight experiment traceability; 
    #     it is NOT a full observability or alerting system.
        
    #     For production observability, you would use:
    #     - Prometheus + Grafana (metrics)
    #     - ELK stack (logs)
    #     - PagerDuty (alerts)
        
    #     MLflow here is just for historical record-keeping and debugging.
    #     """
    #     try:
    #         with mlflow.start_run(run_name=f"monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
    #             mlflow.log_param("job_type", "monitoring")
                
    #             # Log window metadata
    #             if 'analysis_window' in results:
    #                 window = results['analysis_window']
    #                 mlflow.log_param("lookback_hours", window.get('lookback_hours'))
    #                 mlflow.log_param("num_predictions", window.get('num_predictions'))
    #                 mlflow.log_param("window_start", window.get('start_time'))
    #                 mlflow.log_param("window_end", window.get('end_time'))
                
    #             # Log proxy metrics
    #             if 'proxy_metrics' in results and 'overall_stats' in results['proxy_metrics']:
    #                 stats = results['proxy_metrics']['overall_stats']
    #                 if 'num_predictions' in stats:
    #                     mlflow.log_metric("positive_rate", stats.get('positive_rate', 0))
    #                     mlflow.log_metric("probability_mean", stats.get('probability_mean', 0))
    #                     mlflow.log_metric("probability_std", stats.get('probability_std', 0))
                
    #             # Log drift metrics (as numbers, not judgments)
    #             if 'drift_detection' in results:
    #                 drift = results['drift_detection']
    #                 if 'drift_share' in drift:
    #                     mlflow.log_metric("drift_share", drift['drift_share'])
    #                     mlflow.log_metric("num_drifted_features", drift.get('num_drifted_features', 0))
                
    #             logger.debug("Results logged to MLflow for historical record")
        
    #     except Exception as e:
    #         logger.warning(f"MLflow logging failed (non-critical): {e}")


def run_monitoring_job(lookback_hours: int = 24):
    """Convenience function to run monitoring job."""
    job = MonitoringJob()
    return job.run(lookback_hours)

if __name__ == "__main__":
    run_monitoring_job()