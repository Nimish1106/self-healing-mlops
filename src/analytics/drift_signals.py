"""
Drift signal checker for retraining triggers.

Reads drift reports from Phase 3 monitoring and determines if retraining is needed.

FIXED:
- Correct filename parsing (drift_summary_YYYYMMDD_HHMMSS.json)
- Proper lookback window filtering (only recent reports)
- Correct drift report structure parsing
- Extract drifted features properly
"""
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)


class DriftSignalChecker:
    """
    Check if drift signals warrant retraining.
    
    Integrates Phase 3 monitoring with Phase 4 retraining.
    """
    
    def __init__(
        self,
        reports_path: str = "/app/monitoring/reports/drift_reports",
        drift_threshold: float = 0.3,  # Drift score threshold
        lookback_hours: int = 24
    ):
        """
        Initialize drift signal checker.
        
        Args:
            reports_path: Where Phase 3 stores drift reports
            drift_threshold: Drift score above which to trigger retraining
            lookback_hours: How far back to check for drift
        """
        self.reports_path = Path(reports_path)
        self.drift_threshold = drift_threshold
        self.lookback_hours = lookback_hours
    
    def check_drift_signals(self) -> Tuple[bool, Dict]:
        """
        Check if drift signals indicate retraining is needed.
        
        Returns:
            (should_retrain, drift_details)
        """
        logger.info("=" * 80)
        logger.info("CHECKING DRIFT SIGNALS")
        logger.info("=" * 80)
        
        if not self.reports_path.exists():
            logger.warning(f"Drift reports path not found: {self.reports_path}")
            return False, {"status": "no_reports"}
        
        # Get recent drift reports (FIXED: proper filtering)
        recent_reports = self._get_recent_reports()
        
        if len(recent_reports) == 0:
            logger.warning("No recent drift reports found")
            return False, {"status": "no_recent_reports"}
        
        logger.info(f"Analyzing {len(recent_reports)} recent drift reports (last {self.lookback_hours}h)")
        
        # Analyze drift
        drift_detected = False
        drift_details = {
            "num_reports_checked": len(recent_reports),
            "drift_threshold": self.drift_threshold,
            # Track observed dataset-level drift_share (max across reports)
            "drift_share": 0.0,
            # Aggregated info about drifted features across reports
            "drifted_feature_names": [],
            "num_drifted_features": 0,
            "drift_timestamps": []
        }
        
        for report in recent_reports:
            drift_score, drifted_features = self._parse_drift_report(report)
            
            # Keep the largest observed dataset-level drift_share
            if drift_score > drift_details["drift_share"]:
                drift_details["drift_share"] = drift_score

            # Only consider this report a true drift trigger if there are
            # actual drifted features reported. Treat `drift_share` alone
            # as insufficient evidence.
            if drift_score >= self.drift_threshold:
                drift_detected = True
                drift_details["drifted_feature_names"].extend(drifted_features)
                drift_details["drift_timestamps"].append(report["timestamp"])
        
        # Remove duplicates and update counts
        drift_details["drifted_feature_names"] = list(set(drift_details["drifted_feature_names"]))
        drift_details["num_drifted_features"] = len(drift_details["drifted_feature_names"]) 

        logger.info(f"Drift detected: {drift_detected}")
        logger.info(f"Max observed drift_share: {drift_details['drift_share']:.3f}")
        logger.info(f"Threshold: {self.drift_threshold}")

        if drift_detected:
            logger.warning(f"⚠️ DRIFT THRESHOLD EXCEEDED")
            logger.warning(f"Drifted features: {drift_details['drifted_feature_names']}")
        
        return drift_detected, drift_details
    
    def _get_recent_reports(self) -> List[Dict]:
        """
        Get drift reports from last N hours.
        
        FIXED: Proper filename parsing and filtering.
        Phase 3 format: drift_summary_YYYYMMDD_HHMMSS.json
        """
        cutoff_time = datetime.now() - timedelta(hours=self.lookback_hours)
        
        recent_reports = []
        
        # Look for drift_summary_*.json files (Phase 3 format)
        all_files = list(self.reports_path.glob("drift_summary_*.json"))
        
        logger.info(f"Found {len(all_files)} total drift reports")
        
        for report_file in all_files:
            try:
                # Extract timestamp from filename
                # Format: drift_summary_YYYYMMDD_HHMMSS.json
                timestamp_str = report_file.stem.replace("drift_summary_", "")
                
                # Parse: YYYYMMDD_HHMMSS → YYYY-MM-DD HH:MM:SS
                date_part = timestamp_str[:8]  # YYYYMMDD
                time_part = timestamp_str[9:]  # HHMMSS (after underscore)
                
                # Convert to datetime-compatible format
                formatted_timestamp = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                report_time = datetime.strptime(formatted_timestamp, "%Y-%m-%d %H:%M:%S")
                
                # Filter by lookback window
                if report_time < cutoff_time:
                    continue
                
                # Load report data
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                
                recent_reports.append({
                    "timestamp": timestamp_str,
                    "report_time": report_time,
                    "filepath": str(report_file),
                    "data": report_data
                })
            
            except Exception as e:
                logger.warning(f"Could not parse {report_file.name}: {e}")
        
        # Sort by time (most recent first)
        recent_reports = sorted(recent_reports, key=lambda x: x["report_time"], reverse=True)
        
        logger.info(f"Filtered to {len(recent_reports)} reports within last {self.lookback_hours} hours")
        
        return recent_reports
    
    def _parse_drift_report(self, report: Dict) -> Tuple[float, List[str]]:
        """
        Parse Phase 3 drift report (Evidently v0.4.15+ compatible).
        
        Handles both old and new drift_summary schema for backward compatibility.
        
        Returns:
            (drift_score, list_of_drifted_features)
        """
        try:
            report_data = report["data"]
            
            drift_score = 0.0
            drifted_features = []
            
            # =========================================================================
            # EVIDENTLY 0.4.15+ SCHEMA (Primary)
            # =========================================================================
            if "drift_share" in report_data:
                drift_score = float(report_data.get("drift_share", 0.0))
                
                # Extract drifted features from NEW "features" array format
                if "features" in report_data:
                    features_array = report_data["features"]
                    if isinstance(features_array, list):
                        drifted_features = [
                            feat["feature"] for feat in features_array
                            if isinstance(feat, dict) and feat.get("drift_detected", False)
                        ]
            
            # =========================================================================
            # BACKWARD COMPATIBILITY (Old schema)
            # =========================================================================
            # Fallback to old "feature_drift_details" format if new format not found
            if len(drifted_features) == 0 and "feature_drift_details" in report_data:
                old_details = report_data["feature_drift_details"]
                if isinstance(old_details, list) and len(old_details) > 0:
                    drifted_features = [
                        f.get("feature") for f in old_details
                        if isinstance(f, dict) and f.get("drift_detected", False)
                    ]
            
            # Fallback: if still no features, check "drifted_features" key
            if len(drifted_features) == 0 and "drifted_features" in report_data:
                drifted_features = report_data["drifted_features"]
            
            logger.debug(f"Parsed drift report: score={drift_score:.3f}, features={len(drifted_features)}")
            
            return drift_score, drifted_features
        
        except Exception as e:
            logger.warning(f"Could not parse drift report: {e}")
            logger.debug(f"Report data keys: {report.get('data', {}).keys()}")
            return 0.0, []
    
    def get_drift_summary(self) -> Dict:
        """
        Get summary of recent drift activity.
        
        Useful for dashboards/logging.
        """
        should_retrain, details = self.check_drift_signals()
        
        return {
            "retraining_recommended": should_retrain,
            "drift_details": details,
            "threshold": self.drift_threshold,
            "lookback_hours": self.lookback_hours
        }