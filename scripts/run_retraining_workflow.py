"""
Manual retraining workflow (runs outside Airflow).

Usage:
    docker-compose exec api python scripts/run_retraining_workflow.py
"""

import sys

sys.path.append("/app")

from src.storage.prediction_logger import get_prediction_logger
from src.storage.label_store import get_label_store
from src.retraining.shadow_trainer import ShadowModelTrainer
from src.analytics.model_evaluator import ModelEvaluator
from src.retraining.evaluation_gate import EvaluationGate
from src.retraining.model_promoter import ModelPromoter
import pandas as pd
import mlflow
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Execute complete retraining workflow manually."""

    logger.info("=" * 80)
    logger.info("MANUAL RETRAINING WORKFLOW")
    logger.info("=" * 80)

    # Step 1: Check data
    logger.info("\n[Step 1/5] Checking data availability...")

    pred_logger = get_prediction_logger()
    label_store = get_label_store()

    predictions_df = pred_logger.get_predictions_with_features()

    if predictions_df.empty:
        logger.error("No predictions available. Run API and generate predictions first.")
        return

    coverage = label_store.get_label_coverage(predictions_df)
    logger.info(f"  Total predictions: {coverage['total_predictions']}")
    logger.info(f"  Labeled: {coverage['labeled_predictions']}")
    logger.info(f"  Coverage: {coverage['coverage_rate']*100:.1f}%")

    from src.analytics.drift_signals import DriftSignalChecker

    drift_checker = DriftSignalChecker(drift_threshold=0.3)
    drift_detected, drift_details = drift_checker.check_drift_signals()

    logger.info(f"  Drift detected: {drift_detected}")
    if drift_detected:
        logger.warning(f"  ⚠️ Drift score: {drift_details['max_drift_score']:.3f}")

    if coverage["labeled_predictions"] < 100:
        logger.error(f"Insufficient labels: {coverage['labeled_predictions']} < 100")
        logger.info("Run scripts/simulate_traffic.py to generate test data")
        return

    # Step 2: Train shadow model
    logger.info("\n[Step 2/5] Training shadow model...")

    labels_df = pd.read_csv("/app/monitoring/labels/labels.csv")

    trainer = ShadowModelTrainer()

    # Compute temporal windows dynamically from data
    predictions_df["application_date"] = pd.to_datetime(predictions_df["application_date"])

    # Sort by application_date to split chronologically
    sorted_preds = predictions_df.sort_values("application_date").reset_index(drop=True)

    # Use percentage-based split (70% train, 30% eval)
    split_idx = int(len(sorted_preds) * 0.7)

    # Get boundary dates
    train_end = sorted_preds.iloc[split_idx]["application_date"]
    eval_start = train_end + pd.Timedelta(seconds=1)  # Start eval right after train
    eval_end = sorted_preds["application_date"].max() + pd.Timedelta(seconds=1)

    logger.info(
        f"Using temporal windows: train_end={train_end.date()}, eval_start={eval_start.date()}, eval_end={eval_end.date()}"
    )
    logger.info(
        f"  (70% train={split_idx} samples, 30% eval={len(sorted_preds)-split_idx} samples)"
    )

    X_train, X_eval, y_train, y_eval = trainer.prepare_training_data_temporal(
        predictions_df=predictions_df,
        labels_df=labels_df,
        train_end_date=str(train_end),
        eval_start_date=str(eval_start),
        eval_end_date=str(eval_end),
    )

    model, run_id = trainer.train_shadow_model(
        X_train, y_train, X_eval, y_eval, trigger_reason="manual_workflow"
    )

    logger.info(f"  Shadow model: {run_id}")

    # Get versions
    mlflow.set_tracking_uri("http://mlflow:5000")
    client = mlflow.tracking.MlflowClient()

    shadow_versions = client.search_model_versions(
        f"name='credit-risk-model' and run_id='{run_id}'"
    )
    shadow_version = shadow_versions[0].version if shadow_versions else None

    prod_versions = client.get_latest_versions("credit-risk-model", stages=["Production"])

    if not prod_versions:
        logger.info("  No production model - this will be first deployment")
        prod_version = None
    else:
        prod_version = prod_versions[0].version

    # Step 3: Replay evaluation
    logger.info("\n[Step 3/5] Running replay-based evaluation...")

    if prod_version:
        labeled_df = label_store.get_labeled_predictions(predictions_df)
        labeled_df["application_date"] = pd.to_datetime(labeled_df["application_date"])

        # Use same eval window as training
        eval_df = labeled_df[
            (labeled_df["application_date"] >= eval_start)
            & (labeled_df["application_date"] < eval_end)
        ].copy()

        logger.info(f"  Evaluation samples: {len(eval_df)}")

        evaluator = ModelEvaluator()

        prod_metrics, shadow_metrics = evaluator.replay_evaluation(
            eval_df=eval_df,
            production_model_version=prod_version,
            shadow_model_version=shadow_version,
            feature_columns=ShadowModelTrainer.FEATURE_COLUMNS,
        )

        comparison = evaluator.compare_models(prod_metrics, shadow_metrics)

        logger.info(f"  F1 improvement: {comparison['f1_improvement_pct']:+.2f}%")
        logger.info(f"  Brier change: {comparison['brier_change']:+.4f}")
    else:
        # First deployment
        logger.info("  Skipping comparison (first deployment)")
        prod_metrics = None
        shadow_metrics = {"num_samples": len(X_eval)}
        comparison = None

    # Step 4: Evaluation gate
    logger.info("\n[Step 4/5] Running evaluation gate...")

    if prod_version:
        gate = EvaluationGate(
            min_f1_improvement_pct=2.0,
            max_brier_degradation=0.01,
            max_segment_regression_pct=5.0,
            min_samples_for_decision=200,
            min_coverage_pct=30.0,
            promotion_cooldown_days=7,
        )

        should_promote, decision = gate.evaluate(
            production_metrics=prod_metrics,
            shadow_metrics=shadow_metrics,
            comparison=comparison,
            coverage_stats=coverage,
        )
    else:
        # First deployment - auto-promote
        should_promote = True
        decision = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "final_decision": True,
            "reason": ["First model deployment"],
        }

    logger.info(f"  Decision: {'PROMOTE' if should_promote else 'REJECT'}")
    logger.info(f"  Reason: {decision['reason']}")

    # Step 5: Promote or reject
    logger.info("\n[Step 5/5] Executing decision...")

    promoter = ModelPromoter()

    if should_promote:
        result = promoter.promote_to_production(
            shadow_run_id=run_id, evaluation_decision=decision, promoted_by="manual_workflow"
        )

        if result["success"]:
            logger.info(f"  ✅ Promoted: v{result['new_production_version']}")
        else:
            logger.error(f"  ❌ Promotion failed: {result.get('error')}")
    else:
        result = promoter.reject_shadow_model(
            shadow_run_id=run_id, evaluation_decision=decision, rejected_by="manual_workflow"
        )
        logger.info("  ✅ Rejection recorded (gate worked correctly)")

    logger.info("\n" + "=" * 80)
    logger.info("WORKFLOW COMPLETE")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
