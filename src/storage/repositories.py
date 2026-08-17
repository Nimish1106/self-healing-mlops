"""
Repository layer (CORRECTED).

Fixes:
1. Removed num_labeled, coverage_pct from monitoring_metrics
2. Renamed drift_share → feature_drift_ratio
3. Removed gate_results JSONB
4. Fixed SQL INTERVAL parameterization bug
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
import logging
from .db_manager import get_db_manager

logger = logging.getLogger(__name__)


class MonitoringMetricsRepository:
    """
    Repository for monitoring_metrics table.

    ✅ CRITICAL: This table does NOT track labels (asynchronous).
    """

    def __init__(self):
        self.db = get_db_manager()

    def insert(
        self,
        timestamp: datetime,
        lookback_hours: int,
        num_predictions: int,
        proxy_metrics: Dict,
        drift_summary: Dict,
        drift_summary_ref: str = None,
    ) -> str:
        """
        Insert monitoring metrics.

        ✅ FIXED: Removed num_labeled, coverage_pct (don't belong here)
        ✅ FIXED: Renamed drift_share → feature_drift_ratio
        ✅ REMOVED: drift_report_ref (not needed, we have drift_summary_ref)

        Args:
            timestamp: Monitoring run timestamp
            lookback_hours: Lookback window
            num_predictions: Number of predictions analyzed
            proxy_metrics: Dict with proxy metrics
            drift_summary: Dict with drift detection results
            drift_summary_ref: Reference to drift summary file

        Returns:
            Record ID (UUID)
        """
        record_id = str(uuid.uuid4())

        query = """
        INSERT INTO monitoring_metrics (
            id, timestamp, lookback_hours, num_predictions,
            positive_rate, probability_mean, probability_std, entropy,
            dataset_drift_detected, feature_drift_ratio, num_drifted_features,
            drift_summary_ref
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        params = (
            record_id,
            timestamp,
            lookback_hours,
            num_predictions,
            proxy_metrics.get("positive_rate"),
            proxy_metrics.get("probability_mean"),
            proxy_metrics.get("probability_std"),
            proxy_metrics.get("entropy"),
            drift_summary.get("dataset_drift_detected", False),
            drift_summary.get("feature_drift_ratio", 0.0),  # ✅ RENAMED
            drift_summary.get("num_drifted_features", 0),
            drift_summary_ref,
        )

        self.db.execute_query(query, params)
        logger.info(f"Inserted monitoring metrics: {record_id}")

        return record_id

    def get_recent(self, limit: int = 100) -> List[Dict]:
        """Get recent monitoring metrics."""
        query = """
        SELECT * FROM v_recent_monitoring
        LIMIT %s
        """

        rows = self.db.execute_query(query, (limit,))

        columns = [
            "timestamp",
            "num_predictions",
            "feature_drift_ratio",
            "dataset_drift_detected",
            "positive_rate",
            "entropy",
        ]

        return [dict(zip(columns, row)) for row in rows]

    def get_drift_trend(self, days: int = 7) -> List[Dict]:
        """
        Get drift trend over time.

        ✅ FIXED: SQL INTERVAL parameterization bug
        """
        query = """
        SELECT
            timestamp,
            feature_drift_ratio,
            num_drifted_features,
            dataset_drift_detected
        FROM monitoring_metrics
        WHERE timestamp > NOW() - (%s * INTERVAL '1 day')
        ORDER BY timestamp
        """

        rows = self.db.execute_query(query, (days,))  # ✅ FIXED

        columns = [
            "timestamp",
            "feature_drift_ratio",
            "num_drifted_features",
            "dataset_drift_detected",
        ]
        return [dict(zip(columns, row)) for row in rows]


class RetrainingDecisionsRepository:
    """
    Repository for retraining_decisions table.

    ✅ ADDED: labeled_samples, coverage_pct (moved FROM monitoring_metrics)
    ✅ REMOVED: gate_results JSONB (store in files)
    """

    def __init__(self):
        self.db = get_db_manager()

    def insert(
        self,
        timestamp: datetime,
        trigger_reason: str,
        action: str,
        drift_context: Dict,
        data_context: Dict,
        decision_details: Dict,
    ) -> str:
        """
        Insert retraining decision.

        ✅ FIXED: Removed gate_results JSONB
        ✅ FIXED: Renamed drift_share → feature_drift_ratio
        ✅ ADDED: labeled_samples, coverage_pct

        Args:
            timestamp: Decision timestamp
            trigger_reason: Why retraining was considered (scheduled/manual/drift_alert)
            action: Decision outcome (train/skip/promote/reject)
            drift_context: Drift information at decision time
            data_context: Data availability context (labels, coverage)
            decision_details: Gate results, reason, etc.

        Returns:
            Decision ID (UUID)
        """
        decision_id = str(uuid.uuid4())

        query = """
        INSERT INTO retraining_decisions (
            id, timestamp, trigger_reason, action,
            feature_drift_ratio, num_drifted_features, dataset_drift_detected, drifted_features,
            labeled_samples, coverage_pct,
            failed_gate, reason,
            shadow_model_version, production_model_version,
            f1_improvement_pct, brier_change,
            drift_summary_ref, evaluation_report_ref
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        # Normalize data_context
        labeled_samples = None
        coverage_pct = None
        if data_context:
            if "labeled_samples" in data_context and data_context["labeled_samples"] is not None:
                labeled_samples = int(data_context["labeled_samples"])
            elif "labeled_predictions" in data_context and data_context["labeled_predictions"] is not None:
                labeled_samples = int(data_context["labeled_predictions"])

            if "coverage_pct" in data_context and data_context["coverage_pct"] is not None:
                coverage_pct = float(data_context["coverage_pct"])
            elif "label_coverage_pct" in data_context and data_context["label_coverage_pct"] is not None:
                coverage_pct = float(data_context["label_coverage_pct"])
            elif "coverage_rate" in data_context and data_context["coverage_rate"] is not None:
                coverage_pct = float(data_context["coverage_rate"]) * 100.0

        # Normalize drift_context
        feature_drift_ratio = None
        num_drifted_features = 0
        dataset_drift_detected = False
        drifted_features = []
        if drift_context:
            if "feature_drift_ratio" in drift_context and drift_context["feature_drift_ratio"] is not None:
                feature_drift_ratio = float(drift_context["feature_drift_ratio"])
            elif "drift_share" in drift_context and drift_context["drift_share"] is not None:
                feature_drift_ratio = float(drift_context["drift_share"])

            num_drifted_features = int(
                drift_context.get(
                    "num_drifted_features",
                    len(drift_context.get("drifted_features", drift_context.get("drifted_feature_names", []))),
                )
            )
            dataset_drift_detected = bool(drift_context.get("dataset_drift_detected", False))
            drifted_features = drift_context.get(
                "drifted_features", drift_context.get("drifted_feature_names", [])
            )

        params = (
            decision_id,
            timestamp,
            trigger_reason,
            action,
            feature_drift_ratio,
            num_drifted_features,
            dataset_drift_detected,
            drifted_features,
            labeled_samples,
            coverage_pct,
            decision_details.get("failed_gate"),
            decision_details.get("reason"),
            decision_details.get("shadow_model_version"),
            decision_details.get("production_model_version"),
            decision_details.get("f1_improvement_pct"),
            decision_details.get("brier_change"),
            decision_details.get("drift_summary_ref"),
            decision_details.get("evaluation_report_ref"),
        )

        self.db.execute_query(query, params)
        logger.info(f"Inserted retraining decision: {decision_id} (action={action})")

        return decision_id

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get decision history."""
        query = """
        SELECT * FROM v_decision_history
        LIMIT %s
        """

        rows = self.db.execute_query(query, (limit,))

        columns = [
            "timestamp",
            "action",
            "trigger_reason",
            "feature_drift_ratio",
            "labeled_samples",
            "coverage_pct",
            "failed_gate",
            "reason",
            "shadow_model_version",
            "production_model_version",
        ]

        return [dict(zip(columns, row)) for row in rows]

    def count_by_action(self) -> Dict:
        """Count decisions by action."""
        query = """
        SELECT action, COUNT(*) as count
        FROM retraining_decisions
        GROUP BY action
        """

        rows = self.db.execute_query(query)
        return {row[0]: row[1] for row in rows}


class ModelVersionsRepository:
    """
    Repository for model_versions table.

    ✅ CONSTRAINT ENFORCED: Only ONE model in Production (via partial unique index)
    """

    def __init__(self):
        self.db = get_db_manager()

    def insert(
        self,
        model_name: str,
        version: Any,
        stage: str = "Archived",
        training_context: Dict = None,
        metrics: Dict = None,
        decision_id: str = None,
        **kwargs,
    ):
        """
        Insert model version (delegates to insert_or_update with normalized parameters).
        """
        if training_context is None:
            training_context = {}

        if "mlflow_run_id" in kwargs and "training_run_id" not in training_context:
            training_context["training_run_id"] = kwargs["mlflow_run_id"]
        if "status" in kwargs and stage == "Archived":
            stage = "Archived" if kwargs["status"] == "rejected" else kwargs["status"]
        if "timestamp" in kwargs and "archived_at" not in training_context:
            training_context["archived_at"] = str(kwargs["timestamp"])

        return self.insert_or_update(
            model_name=model_name,
            version=int(version),
            stage=stage,
            training_context=training_context,
            metrics=metrics,
            decision_id=decision_id,
        )

    def insert_or_update(
        self,
        model_name: str,
        version: Any,
        stage: str,
        training_context: Dict = None,
        metrics: Dict = None,
        decision_id: str = None,
    ):
        """
        Insert or update model version.

        ✅ Database enforces: Only ONE model can be in Production
        (Will raise error if violated)
        """
        if training_context is None:
            training_context = {}

        query = """
        INSERT INTO model_versions (
            model_name, version, stage,
            trained_at, promoted_at, archived_at,
            trigger_reason, training_run_id,
            f1_score, brier_score, num_samples,
            feature_drift_ratio_at_training,
            decision_id
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (model_name, version)
        DO UPDATE SET
            stage = EXCLUDED.stage,
            promoted_at = EXCLUDED.promoted_at,
            archived_at = EXCLUDED.archived_at,
            updated_at = CURRENT_TIMESTAMP
        """

        f1_score = None
        brier_score = None
        num_samples = None

        if metrics:
            if "primary_metrics" in metrics:
                f1_score = metrics["primary_metrics"].get("f1_score")
            elif "f1_score" in metrics:
                f1_score = metrics.get("f1_score")

            if "calibration_metrics" in metrics:
                brier_score = metrics["calibration_metrics"].get("brier_score")
            elif "brier_score" in metrics:
                brier_score = metrics.get("brier_score")

            num_samples = metrics.get("num_samples")

        params = (
            model_name,
            int(version),
            stage,
            training_context.get("trained_at"),
            training_context.get("promoted_at"),
            training_context.get("archived_at"),
            training_context.get("trigger_reason"),
            training_context.get("training_run_id"),
            f1_score,
            brier_score,
            num_samples,
            training_context.get("feature_drift_ratio_at_training"),
            decision_id,
        )

        self.db.execute_query(query, params)
        logger.info(f"Upserted model version: {model_name} v{version} ({stage})")

    def get_timeline(self) -> List[Dict]:
        """Get model promotion timeline."""
        query = "SELECT * FROM v_model_timeline"

        rows = self.db.execute_query(query)

        columns = [
            "model_name",
            "version",
            "stage",
            "trained_at",
            "promoted_at",
            "f1_score",
            "drift_at_training",
            "action",
        ]

        return [dict(zip(columns, row)) for row in rows]
