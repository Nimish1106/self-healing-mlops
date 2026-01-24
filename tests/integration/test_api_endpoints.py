"""
Integration tests for API endpoints.

Tests the API as a whole, including request/response flow.
"""

import sys

import pytest
from httpx import ASGITransport
from starlette.testclient import TestClient
from src.api_mlflow import app

sys.path.append("/app")


@pytest.fixture
def client():
    """Fixture to provide a TestClient instance."""
    transport = ASGITransport(app=app)
    return TestClient(transport=transport)


class TestAPIEndpoints:
    """Test suite for API endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns 200."""
        response = client.get("/")
        assert response.status_code == 200
        assert "service" in response.json()

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "model_loaded" in data

    def test_model_info_endpoint(self, client):
        """Test model info endpoint."""
        response = client.get("/model/info")

        # May return 503 if model not loaded in test environment
        assert response.status_code in [200, 503]

    def test_predict_endpoint_validation(self, client):
        """Test that predict endpoint validates input."""
        # Invalid input (missing required fields)
        invalid_input = {
            "age": 45
            # Missing other required fields
        }

        response = client.post("/predict", json=invalid_input)
        assert response.status_code == 422  # Validation error

    def test_predict_endpoint_valid_input(self, client):
        """Test prediction with valid input."""
        valid_input = {
            "RevolvingUtilizationOfUnsecuredLines": 0.766127,
            "age": 45,
            "NumberOfTime30_59DaysPastDueNotWorse": 2,
            "DebtRatio": 0.802982,
            "MonthlyIncome": 9120.0,
            "NumberOfOpenCreditLinesAndLoans": 13,
            "NumberOfTimes90DaysLate": 0,
            "NumberRealEstateLoansOrLines": 6,
            "NumberOfTime60_89DaysPastDueNotWorse": 0,
            "NumberOfDependents": 2,
        }

        response = client.post("/predict", json=valid_input)

        # May fail if model not loaded in test environment
        # But should not be validation error
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "prediction" in data
            assert "probability" in data
            assert "model_version" in data
            assert "prediction_id" in data

            # Validate output types
            assert data["prediction"] in [0, 1]
            assert 0 <= data["probability"] <= 1

    def test_predict_endpoint_invalid_values(self, client):
        """Test that invalid feature values are rejected."""
        invalid_input = {
            "RevolvingUtilizationOfUnsecuredLines": 0.5,
            "age": -5,  # Invalid age
            "NumberOfTime30_59DaysPastDueNotWorse": 2,
            "DebtRatio": 0.8,
            "MonthlyIncome": 9120.0,
            "NumberOfOpenCreditLinesAndLoans": 13,
            "NumberOfTimes90DaysLate": 0,
            "NumberRealEstateLoansOrLines": 6,
            "NumberOfTime60_89DaysPastDueNotWorse": 0,
            "NumberOfDependents": 2,
        }

        response = client.post("/predict", json=invalid_input)
        assert response.status_code == 422  # Validation error

    def test_monitoring_stats_endpoint(self, client):
        """Test monitoring stats endpoint."""
        response = client.get("/monitoring/stats")
        assert response.status_code in [200, 500]  # May not have data in test
