"""
Unit tests for proxy metrics calculation.

Tests the calculation of proxy metrics for model monitoring.
"""
import pytest
import pandas as pd
import numpy as np
import sys

sys.path.append("/app")
from src.analytics.proxy_metrics import ProxyMetricsCalculator


class TestProxyMetricsCalculator:
    """Test suite for ProxyMetricsCalculator class."""

    def test_initialization(self):
        """Test ProxyMetricsCalculator initializes correctly."""
        calculator = ProxyMetricsCalculator()
        assert calculator is not None

    def test_calculate_prediction_entropy(self, sample_predictions_df):
        """Test entropy calculation from predictions."""
        calculator = ProxyMetricsCalculator()

        # Get sample of predictions
        predictions = sample_predictions_df["probability"].values

        # Calculate entropy
        entropy = calculator.calculate_entropy(predictions)

        # Entropy should be between 0 and 1 for probabilities
        assert 0 <= entropy <= 1

    def test_calculate_class_imbalance(self, sample_predictions_df):
        """Test class imbalance metric calculation."""
        calculator = ProxyMetricsCalculator()

        predictions = sample_predictions_df["prediction"].values

        # Calculate imbalance
        imbalance = calculator.calculate_class_imbalance(predictions)

        # Imbalance ratio should be > 0
        assert imbalance > 0

    def test_calculate_prediction_drift_signal(self, sample_predictions_df):
        """Test prediction drift signal calculation."""
        calculator = ProxyMetricsCalculator()

        # Get two samples
        ref_predictions = sample_predictions_df.iloc[:100]["probability"].values
        current_predictions = sample_predictions_df.iloc[100:200]["probability"].values

        # Calculate drift signal
        signal = calculator.calculate_drift_signal(ref_predictions, current_predictions)

        assert isinstance(signal, dict)
        assert "drift_magnitude" in signal
        assert signal["drift_magnitude"] >= 0
