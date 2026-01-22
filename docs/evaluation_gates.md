# Evaluation Gate Criteria

## Overview

The **Evaluation Gate** is the automated decision-making system that determines whether a shadow model should be promoted to production. It implements a multi-stage gating mechanism with strict criteria.

## Gate Architecture

```
Shadow Model
    ↓
┌─────────────────────────────────────┐
│     GATE 1: Sample Validity         │
│  Require: ≥200 samples for decision │
└────────────┬────────────────────────┘
             │
        ✅ YES / ❌ NO
             │
             ↓
┌─────────────────────────────────────┐
│    GATE 2: Performance Improvement  │
│  Require: F1 Score +2.0% minimum    │
└────────────┬────────────────────────┘
             │
        ✅ YES / ❌ NO
             │
             ↓
┌─────────────────────────────────────┐
│   GATE 3: Calibration Quality       │
│  Require: Brier Score degradation   │
│           ≤ 0.01 (1%)               │
└────────────┬────────────────────────┘
             │
        ✅ YES / ❌ NO
             │
             ↓
┌─────────────────────────────────────┐
│    GATE 4: Segment Fairness         │
│  Require: No regression on segments │
└────────────┬────────────────────────┘
             │
        ✅ ALL PASS / ❌ ANY FAIL
             │
       ┌─────┴─────┐
       ↓           ↓
   PROMOTE     ARCHIVE
```

---

## Gate 1: Sample Validity

### Criterion: Minimum Samples (≥200)

**Purpose:** Ensure statistical validity of evaluation

**Rationale:**
- F1 Score requires >= 20-30 positive samples
- With ~10% positive class, need ~300 total samples
- Conservative: require 200 samples minimum

### Configuration

```python
gate = EvaluationGate(
    min_samples_for_decision=200  # Configurable
)
```

### Metric Used

```
num_samples = min(
    len(production_metrics['samples']),
    len(shadow_metrics['samples'])
)
```

### Rejection Reason

```
"Insufficient samples ({num_samples} < 200).
 Need more labeled predictions before evaluation."
```

### Why This Matters

Without enough samples:
- ❌ F1 Score becomes unreliable
- ❌ Statistical tests lack power
- ❌ Could promote mediocre models by chance
- ❌ Unfair comparison with production model

**Minimum samples per class:**
- Negative class: ~180 (90% of 200)
- Positive class: ~20 (10% of 200)

---

## Gate 2: Performance Improvement

### Criterion: F1 Score Improvement (≥2.0%)

**Purpose:** Ensure model actually improves predictions

**Rationale:**
- F1 balances precision and recall
- 2% improvement is measurable but realistic
- Avoids promoting marginal improvements
- Prevents over-fitting to test set

### Configuration

```python
gate = EvaluationGate(
    min_f1_improvement_pct=2.0  # Configurable
)
```

### Calculation

```python
# F1 Improvement Percentage
f1_improvement_pct = (
    (shadow_f1 - production_f1) / production_f1 * 100
)

# Example:
# Production F1: 0.800
# Shadow F1: 0.820
# Improvement: (0.820 - 0.800) / 0.800 * 100 = 2.5% ✅ PASS
```

### Rejection Reason

```
"Insufficient F1 improvement ({improvement_pct:.2f}% < 2.0%).
 Model must show measurable performance gain."
```

### Why This Matters

- 2% improvement is NOT significant by chance
  - With 200 samples, p-value would be < 0.05
  - Statistically significant at 95% confidence
- Prevents churn from micro-improvements
- Avoids deployment costs for minimal gains

### F1 Score Interpretation

```
F1 = 2 * (Precision * Recall) / (Precision + Recall)

High F1 means:
- ✅ Few false positives (precision)
- ✅ Few false negatives (recall)
- ✅ Good overall predictions
```

---

## Gate 3: Calibration Quality

### Criterion: Brier Score Degradation (≤0.01)

**Purpose:** Ensure probability estimates don't worsen

**Rationale:**
- Brier Score measures calibration accuracy
- Higher = worse predictions
- Allow ≤1% degradation (0.01)
- Production stability is critical

### Configuration

```python
gate = EvaluationGate(
    max_brier_degradation=0.01  # Configurable
)
```

### Calculation

```python
# Brier Score: MSE of predicted probability vs actual outcome
# Brier = mean((predicted_probability - actual)^2)

# Example:
# Production Brier: 0.150
# Shadow Brier: 0.155
# Degradation: 0.155 - 0.150 = 0.005 ✅ PASS (< 0.01)
```

### Rejection Reason

```
"Calibration degraded ({degradation:.4f} > 0.01).
 Shadow model's probability estimates are less reliable."
```

### Why This Matters

Calibration is critical for:
- ✅ Proper uncertainty quantification
- ✅ Risk scoring systems
- ✅ Decision making in downstream systems
- ✅ Regulatory compliance

Bad calibration can lead to:
- ❌ Over-confident wrong predictions
- ❌ Downstream systems making poor decisions
- ❌ Undetected model drift

### Brier Score Interpretation

```
Brier Score Range: [0, 1]

Examples:
- 0.05  = Excellent (very well calibrated)
- 0.10  = Good (well calibrated)
- 0.15  = Acceptable (reasonably calibrated)
- 0.20  = Poor (poorly calibrated)
- 0.25  = Random guessing (uninformative)
```

---

## Gate 4: Segment Fairness

### Criterion: No Regression on Important Segments

**Purpose:** Ensure equitable performance across groups

**Rationale:**
- Model must improve across ALL important segments
- Cannot trade off one group for another
- Critical for fair/ethical AI
- Regulatory requirement in some jurisdictions

### Configuration

```python
gate = EvaluationGate(
    segment_definitions={
        'age_groups': ['<30', '30-50', '50+'],
        'income_levels': ['low', 'medium', 'high']
    },
    min_segment_f1_improvement_pct=1.0  # 1% per segment
)
```

### Segments Analyzed

```python
segments = {
    'age_groups': {
        '<30': mask_age < 30,
        '30-50': (mask_age >= 30) & (mask_age < 50),
        '50+': mask_age >= 50
    },
    'income_levels': {
        'low': mask_income < quantile_33,
        'medium': (mask_income >= quantile_33) & (mask_income < quantile_67),
        'high': mask_income >= quantile_67
    }
}
```

### Rejection Reason

```
"Segment regression detected. Model performs worse on:
 - Age <30: -1.5% F1 (was 0.75, now 0.74)
 - Low income: -0.8% F1 (was 0.70, now 0.69)
 Shadow model must improve or maintain all segments."
```

### Why This Matters

Segment regression creates:
- ❌ Unfair outcomes for certain groups
- ❌ Discrimination (potentially illegal)
- ❌ Brand/reputation damage
- ❌ Regulatory violations

### Example Scenario

```
REJECTED MODEL:
╔════════════════╦══════════╦══════════╦══════════╗
║ Segment        ║ Prod F1  ║ Shadow F1║ Change   ║
╠════════════════╬══════════╬══════════╬══════════╣
║ Overall        ║ 0.800    ║ 0.825    ║ +3.1% ✅ ║
║ Age <30        ║ 0.750    ║ 0.735    ║ -2.0% ❌ ║
║ 30-50          ║ 0.810    ║ 0.830    ║ +2.5% ✅ ║
║ 50+            ║ 0.790    ║ 0.815    ║ +3.2% ✅ ║
║ Low Income     ║ 0.700    ║ 0.690    ║ -1.4% ❌ ║
║ Med Income     ║ 0.820    ║ 0.835    ║ +1.8% ✅ ║
║ High Income    ║ 0.850    ║ 0.870    ║ +2.4% ✅ ║
╚════════════════╩══════════╩══════════╩══════════╝

DECISION: REJECT
Reason: Regression detected in 2 segments
```

---

## Combined Gate Logic

All gates must pass for promotion:

```python
all_gates_pass = (
    samples_valid
    AND f1_improved
    AND calibration_ok
    AND no_segment_regression
)

if all_gates_pass:
    promote_to_production()
else:
    archive_shadow_model()
```

### Example: All Gates Pass

```
Shadow Model Evaluation Results:
═══════════════════════════════════════════════════

GATE 1: Sample Validity
  Status: ✅ PASS
  Samples: 250 >= 200 required

GATE 2: Performance Improvement
  Status: ✅ PASS
  F1 Improvement: 3.2% >= 2.0% required
  Production F1: 0.800 → Shadow F1: 0.826

GATE 3: Calibration Quality
  Status: ✅ PASS
  Brier Degradation: 0.003 <= 0.01 allowed
  Production Brier: 0.150 → Shadow Brier: 0.153

GATE 4: Segment Fairness
  Status: ✅ PASS
  All segments improved (min +0.5%)
  Age <30: +1.2%, 30-50: +2.8%, 50+: +4.1%
  Low income: +0.8%, Med: +2.0%, High: +3.5%

═══════════════════════════════════════════════════
FINAL DECISION: ✅ PROMOTE TO PRODUCTION

Timestamp: 2024-01-15T14:30:00
Model Version: 2
Confidence: 95.2%
```

### Example: Gate Fails

```
Shadow Model Evaluation Results:
═══════════════════════════════════════════════════

GATE 1: Sample Validity
  Status: ✅ PASS
  Samples: 250 >= 200 required

GATE 2: Performance Improvement
  Status: ❌ FAIL
  F1 Improvement: 1.5% < 2.0% required
  Production F1: 0.800 → Shadow F1: 0.812

GATE 3: Calibration Quality
  Status: ✅ PASS
  Brier Degradation: 0.005 <= 0.01 allowed

GATE 4: Segment Fairness
  Status: ✅ PASS
  All segments stable or improved

═══════════════════════════════════════════════════
FINAL DECISION: ❌ REJECT (Archive)

Failure Reasons:
  1. Insufficient F1 improvement (1.5% < 2.0%)

Action: Shadow model archived as experiment 42
Review: Manual inspection recommended
```

---

## Customization

Gates are configurable for different use cases:

### Conservative (High Bar)
```python
gate = EvaluationGate(
    min_samples_for_decision=500,
    min_f1_improvement_pct=5.0,
    max_brier_degradation=0.005,
    enforce_segment_fairness=True
)
```

### Aggressive (Low Bar)
```python
gate = EvaluationGate(
    min_samples_for_decision=100,
    min_f1_improvement_pct=1.0,
    max_brier_degradation=0.05,
    enforce_segment_fairness=False
)
```

### Production Default
```python
gate = EvaluationGate(
    min_samples_for_decision=200,     # Standard
    min_f1_improvement_pct=2.0,       # Measurable
    max_brier_degradation=0.01,       # Stability
    enforce_segment_fairness=True     # Equity
)
```

---

## Monitoring & Alerts

### Track Evaluation Metrics

```bash
# View evaluation history
cat monitoring/metrics/evaluation_results.json | jq

# Alert on repeated failures
if [ $(grep -c '"final_decision": false' monitoring/metrics/evaluation_results.json) -gt 5 ]; then
    echo "⚠️  ALERT: 5+ consecutive shadow model rejections"
fi
```

### Dashboard Integration

```python
# MLflow integration
mlflow.log_metrics({
    'gate_1_pass': 1,
    'gate_2_pass': 1,
    'gate_3_pass': 1,
    'gate_4_pass': 1,
    'promotion_candidate': 1
})
```

---

## FAQ

**Q: Why 2% F1 improvement?**
A: Statistically significant at p<0.05 with 200 samples. Measurable but realistic.

**Q: Can we change gate thresholds?**
A: Yes! Configuration is in `src/retraining/evaluation_gate.py`. But test thoroughly.

**Q: What if gates are too strict?**
A: Use Conservative threshold, collect more data, or improve training process.

**Q: What if gates are too loose?**
A: Risk degraded production models. Recommend Manual Gate 5.

**Q: What about class imbalance?**
A: F1 Score handles imbalance. Brier handles probability accuracy. Segments ensure group fairness.

---

## Related Documentation

- [Architecture Overview](architecture.md)
- [Retraining Pipeline](../src/retraining/evaluation_gate.py)
- [Testing Evaluation Gate](../tests/unit/test_evaluation_gate.py)
