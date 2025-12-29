"""
Proxy metrics for monitoring WITHOUT ground truth labels.

KEY PRINCIPLE: These are TRENDS, not thresholds.
We track how metrics change over time, not whether they cross magic numbers.

WHY NO ACCURACY?
Because we don't have labels yet. Accuracy requires ground truth.
Proxy metrics give us early signals about model behavior changes.

WHAT PROXY METRICS TELL US:
- Is the model seeing different data? (prediction distribution shift)
- Is the model becoming uncertain? (probability spread changes)
- Is there a sudden change? (rate of change detection)

WHAT PROXY METRICS DON'T TELL US:
- Is the model correct? (need labels)
- Should we retrain? (need evaluation gate logic from Phase 4)
- Is this drift "bad"? (requires domain knowledge)
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from scipy.stats import entropy as scipy_entropy
import logging

logger = logging.getLogger(__name__)


def compute_prediction_distribution_stats(predictions: pd.DataFrame) -> Dict:
    """
    Compute statistical summary of prediction distribution.
    
    NO THRESHOLDS. Just descriptive statistics.
    Interpretation happens elsewhere (or by humans).
    """
    if len(predictions) == 0:
        return {"status": "no_data"}
    
    return {
        "num_predictions": len(predictions),
        "positive_rate": float(predictions['prediction'].mean()),
        "probability_mean": float(predictions['probability'].mean()),
        "probability_std": float(predictions['probability'].std()),
        "probability_median": float(predictions['probability'].median()),
        "probability_q25": float(predictions['probability'].quantile(0.25)),
        "probability_q75": float(predictions['probability'].quantile(0.75)),
    }


def compute_probability_entropy(predictions: pd.DataFrame) -> float:
    """
    Compute entropy of probability distribution.
    
    Higher entropy = more spread out probabilities = less decisive model
    Lower entropy = concentrated probabilities = more decisive model
    
    IMPORTANT: This does NOT mean high entropy is bad.
    - High entropy might be correct if data is genuinely ambiguous
    - Low entropy might be wrong if model is overconfident
    
    Entropy is a SIGNAL, not a quality metric.
    """
    if len(predictions) == 0:
        return 0.0
    
    # Bin probabilities
    bins = np.linspace(0, 1, 11)  # 10 bins
    hist, _ = np.histogram(predictions['probability'], bins=bins)
    
    # Normalize
    prob_dist = hist / hist.sum() if hist.sum() > 0 else hist
    
    # Compute Shannon entropy
    return float(scipy_entropy(prob_dist + 1e-10))  # Add epsilon to avoid log(0)


def compute_time_windowed_trends(
    predictions: pd.DataFrame,
    windows: List[str] = ['1H', '6H', '24H']
) -> Dict:
    """
    Compute metrics over multiple time windows.
    
    WHY TIME WINDOWS?
    Because trends matter more than snapshots.
    A sudden change in 1 hour is more concerning than gradual drift over 24 hours.
    
    Args:
        predictions: DataFrame with 'timestamp' column
        windows: List of pandas time offset strings
        
    Returns:
        Dictionary with metrics per time window
    """
    if len(predictions) == 0:
        return {"status": "no_data"}
    
    # Ensure timestamp is datetime
    predictions = predictions.copy()
    predictions['timestamp'] = pd.to_datetime(predictions['timestamp'])
    
    # Sort by time
    predictions = predictions.sort_values('timestamp')
    
    # Current time (latest prediction)
    current_time = predictions['timestamp'].max()
    
    results = {}
    
    for window in windows:
        # Get predictions in this window
        cutoff_time = current_time - pd.Timedelta(window)
        windowed_data = predictions[predictions['timestamp'] > cutoff_time]
        
        if len(windowed_data) == 0:
            results[f'window_{window}'] = {"status": "no_data"}
            continue
        
        results[f'window_{window}'] = {
            "count": len(windowed_data),
            "positive_rate": float(windowed_data['prediction'].mean()),
            "probability_mean": float(windowed_data['probability'].mean()),
            "probability_std": float(windowed_data['probability'].std()),
            "entropy": compute_probability_entropy(windowed_data)
        }
    
    return results


def compute_rate_of_change(
    current_stats: Dict,
    previous_stats: Dict,
    time_delta_hours: float
) -> Dict:
    """
    Compute rate of change between two metric snapshots.
    
    WHY RATE OF CHANGE?
    Absolute values are hard to interpret.
    Rate of change tells us: "Is something changing quickly?"
    
    Example:
    - Positive rate changing from 0.07 to 0.09 over 24 hours: gradual
    - Positive rate changing from 0.07 to 0.15 over 1 hour: sudden (investigate!)
    
    This is MORE INFORMATIVE than thresholds like "alert if > 0.1".
    """
    if not current_stats or not previous_stats:
        return {"status": "insufficient_data"}
    
    # Compute deltas
    positive_rate_delta = current_stats.get('positive_rate', 0) - previous_stats.get('positive_rate', 0)
    probability_mean_delta = current_stats.get('probability_mean', 0) - previous_stats.get('probability_mean', 0)
    
    # Compute rates (per hour)
    rates = {
        "positive_rate_change_per_hour": positive_rate_delta / time_delta_hours if time_delta_hours > 0 else 0,
        "probability_mean_change_per_hour": probability_mean_delta / time_delta_hours if time_delta_hours > 0 else 0,
        "time_delta_hours": time_delta_hours
    }
    
    return rates


def analyze_proxy_metrics(predictions: pd.DataFrame) -> Dict:
    """
    Main entry point for proxy metrics analysis.
    
    Returns comprehensive statistical summary WITHOUT making decisions.
    Decision-making happens in Phase 4 (evaluation gates).
    """
    logger.info(f"Analyzing proxy metrics for {len(predictions)} predictions")
    
    results = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "overall_stats": compute_prediction_distribution_stats(predictions),
        "entropy": compute_probability_entropy(predictions),
        "time_windowed": compute_time_windowed_trends(predictions)
    }
    
    logger.info(f"Proxy metrics computed: {results['overall_stats']['num_predictions']} samples")
    
    return results