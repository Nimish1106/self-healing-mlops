"""
Unit tests for model evaluator logic.

Tests model evaluation and performance metrics calculation.
"""
import pytest
import pandas as pd
import numpy as np
import sys

sys.path.append("/app")
from src.analytics.model_evaluator import ModelEvaluator


class TestModelEvaluator:
    """Test suite for ModelEvaluator class."""

    def test_initialization(self):
        """Test ModelEvaluator initializes correctly."""
        evaluator = ModelEvaluator()
        assert evaluator is not None

    def test_calculate_binary_metrics(self, sample_labels_df):
        """Test binary classification metrics calculation."""
        evaluator = ModelEvaluator()

        # Create true labels and predictions
        y_true = sample_labels_df["true_label"].values
        y_pred = np.random.binomial(1, 0.1, len(y_true))
        y_pred_proba = np.random.beta(2, 8, len(y_true))

        # Calculate metrics
        metrics = evaluator.calculate_metrics(
            y_true=y_true, y_pred=y_pred, y_pred_proba=y_pred_proba
        )

        # Check metrics structure
        assert isinstance(metrics, dict)
        assert "accuracy" in metrics or "f1_score" in metrics

    def test_confusion_matrix_calculation(self, sample_labels_df):
        """Test confusion matrix calculation."""
        evaluator = ModelEvaluator()

        y_true = sample_labels_df["true_label"].values
        y_pred = np.random.binomial(1, 0.1, len(y_true))

        # Calculate confusion matrix
        cm = evaluator.calculate_confusion_matrix(y_true, y_pred)

        assert cm is not None
        assert cm.shape == (2, 2)

    def test_roc_auc_calculation(self, sample_labels_df):
        """Test ROC AUC calculation."""
        evaluator = ModelEvaluator()

        y_true = sample_labels_df["true_label"].values
        y_pred_proba = np.random.beta(2, 8, len(y_true))

        # Calculate ROC AUC
        roc_auc = evaluator.calculate_roc_auc(y_true, y_pred_proba)

        # ROC AUC should be between 0 and 1
        assert 0 <= roc_auc <= 1
