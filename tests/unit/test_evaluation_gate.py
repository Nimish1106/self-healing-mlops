"""
Unit tests for evaluation gate logic.

CRITICAL: These tests verify the decision-making logic
that determines whether shadow models get promoted.
"""

import pytest
import sys

sys.path.append("/app")
from src.retraining.evaluation_gate import EvaluationGate


class TestEvaluationGate:
    """Test suite for EvaluationGate class."""

    def test_gate_passes_on_good_shadow_model(self):
        """Test that gate approves a clearly better model."""
        gate = EvaluationGate(
            min_f1_improvement_pct=2.0, max_brier_degradation=0.01, min_samples_for_decision=200
        )

        production_metrics = {
            "num_samples": 250,
            "primary_metrics": {"f1_score": 0.80, "roc_auc": 0.85},
            "calibration_metrics": {"brier_score": 0.15},
        }

        shadow_metrics = {
            "num_samples": 250,
            "primary_metrics": {"f1_score": 0.84, "roc_auc": 0.87},  # 5% improvement
            "calibration_metrics": {"brier_score": 0.145},  # Slight improvement
        }

        comparison = {"f1_improvement_pct": 5.0, "brier_change": -0.005}

        should_promote, decision = gate.evaluate(production_metrics, shadow_metrics, comparison)

        assert should_promote is True
        assert decision["final_decision"] is True
        assert all(gate["passed"] for gate in decision["gate_results"].values())

    def test_gate_fails_on_insufficient_improvement(self):
        """Test that gate rejects model with insufficient F1 improvement."""
        gate = EvaluationGate(min_f1_improvement_pct=2.0)

        production_metrics = {
            "num_samples": 250,
            "primary_metrics": {"f1_score": 0.80},
            "calibration_metrics": {"brier_score": 0.15},
        }

        shadow_metrics = {
            "num_samples": 250,
            "primary_metrics": {"f1_score": 0.805},  # Only 0.625% improvement
            "calibration_metrics": {"brier_score": 0.15},
        }

        comparison = {"f1_improvement_pct": 0.625, "brier_change": 0.0}

        should_promote, decision = gate.evaluate(production_metrics, shadow_metrics, comparison)

        assert should_promote is False
        assert decision["final_decision"] is False
        assert "Insufficient F1 improvement" in decision["reason"][0]

    def test_gate_fails_on_calibration_degradation(self):
        """Test that gate rejects model with worse calibration."""
        gate = EvaluationGate(min_f1_improvement_pct=2.0, max_brier_degradation=0.01)

        production_metrics = {
            "num_samples": 250,
            "primary_metrics": {"f1_score": 0.80},
            "calibration_metrics": {"brier_score": 0.10},
        }

        shadow_metrics = {
            "num_samples": 250,
            "primary_metrics": {"f1_score": 0.85},  # Better F1
            "calibration_metrics": {"brier_score": 0.15},  # But worse calibration
        }

        comparison = {"f1_improvement_pct": 6.25, "brier_change": 0.05}  # Exceeds threshold

        should_promote, decision = gate.evaluate(production_metrics, shadow_metrics, comparison)

        assert should_promote is False
        assert "Calibration degraded" in decision["reason"][0]

    def test_gate_fails_on_insufficient_samples(self):
        """Test that gate requires minimum sample size."""
        gate = EvaluationGate(min_samples_for_decision=200)

        production_metrics = {"num_samples": 150}
        shadow_metrics = {"num_samples": 150}
        comparison = {}

        should_promote, decision = gate.evaluate(production_metrics, shadow_metrics, comparison)

        assert should_promote is False
        assert "Insufficient samples" in decision["reason"][0]

    def test_threshold_customization(self):
        """Test that custom thresholds work correctly."""
        # Stricter gate
        strict_gate = EvaluationGate(
            min_f1_improvement_pct=5.0, max_brier_degradation=0.005  # Require 5% improvement
        )

        production_metrics = {
            "num_samples": 250,
            "primary_metrics": {"f1_score": 0.80},
            "calibration_metrics": {"brier_score": 0.15},
        }

        shadow_metrics = {
            "num_samples": 250,
            "primary_metrics": {"f1_score": 0.83},  # 3.75% improvement
            "calibration_metrics": {"brier_score": 0.15},
        }

        comparison = {"f1_improvement_pct": 3.75, "brier_change": 0.0}

        should_promote, decision = strict_gate.evaluate(
            production_metrics, shadow_metrics, comparison
        )

        # Should fail strict gate
        assert should_promote is False
