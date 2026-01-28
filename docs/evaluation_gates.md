# Evaluation Gate Criteria

## Overview

The **Evaluation Gate** is an automated decision-making system that determines whether a shadow model should be promoted to production. All 6 gates must pass for promotion (fail-closed design).

---

## Gate Summary

| Gate | Criterion | Threshold | Purpose |
|------|-----------|-----------|---------|
| 1 | Sample Validity | ≥200 samples | Statistical validity |
| 2 | Label Coverage | ≥30% labeled | Reliable evaluation data |
| 3 | Promotion Cooldown | ≥7 days since last | Production stability |
| 4 | Performance Improvement | F1 Score +2.0% min | Measurable improvement |
| 5 | Calibration Quality | Brier degradation ≤0.01 | Probability accuracy |
| 6 | Segment Fairness | No regression on segments | Equitable performance |

---

## Gate Details

### Gate 1: Sample Validity (≥200 samples)
- Ensures F1 Score reliability (requires ~20-30 positive samples)
- With ~10% positive class, need minimum 200 total samples

### Gate 2: Label Coverage (≥30%)
- Not all predictions get labels due to feedback delays
- Prevents bias from sparse/selective labeling patterns

### Gate 3: Promotion Cooldown (≥7 days)
- Prevents deployment churn and retraining storms
- Allows time for monitoring and issue detection
- **Note:** EvaluationGate is the SOLE authority for cooldown enforcement

### Gate 4: Performance Improvement (F1 +2.0%)
```python
f1_improvement_pct = (shadow_f1 - production_f1) / production_f1 * 100
```
- 2% improvement is statistically significant (p<0.05 with 200 samples)

### Gate 5: Calibration Quality (Brier ≤0.01 degradation)
```python
brier_degradation = shadow_brier - production_brier
```
- Critical for uncertainty quantification and downstream decisions
- Brier Score: 0.05=Excellent, 0.10=Good, 0.15=Acceptable, 0.25=Random

### Gate 6: Segment Fairness (No regression)
- Model must maintain/improve across ALL defined segments
- Prevents trading off one group's performance for another
- Segments: age groups, income levels, etc.

---

## Configuration

```python
# Production Default
gate = EvaluationGate(
    min_samples_for_decision=200,
    min_coverage_pct=30.0,
    promotion_cooldown_days=7,
    min_f1_improvement_pct=2.0,
    max_brier_degradation=0.01,
    enforce_segment_fairness=True
)

# Conservative (High Bar)
gate = EvaluationGate(
    min_samples_for_decision=500,
    min_coverage_pct=50.0,
    promotion_cooldown_days=14,
    min_f1_improvement_pct=5.0,
    max_brier_degradation=0.005,
    enforce_segment_fairness=True
)

# Aggressive (Low Bar)
gate = EvaluationGate(
    min_samples_for_decision=100,
    min_coverage_pct=10.0,
    promotion_cooldown_days=1,
    min_f1_improvement_pct=1.0,
    max_brier_degradation=0.05,
    enforce_segment_fairness=False
)
```

---

## Decision Flow

```
Shadow Model → Gate 1 → Gate 2 → Gate 3 → Gate 4 → Gate 5 → Gate 6
                                                              ↓
                                              ALL PASS → PROMOTE
                                              ANY FAIL → ARCHIVE
```

---

## FAQ

| Question | Answer |
|----------|--------|
| Why 30% label coverage? | Large enough to avoid biased evaluation but realistic for production feedback delays |
| Why 7-day cooldown? | Gives monitoring systems time to validate model behavior |
| Why 2% F1 improvement? | Statistically significant at p<0.05 with 200 samples |
| Can cooldown be overridden? | No. EvaluationGate is the sole authority |
| What about class imbalance? | F1 handles imbalance; Brier handles probability accuracy; Segments ensure group fairness |

---

## Related Documentation

- [Architecture Overview](architecture.md)
- [Retraining Pipeline](../src/retraining/evaluation_gate.py)
- [Testing Evaluation Gate](../tests/unit/test_evaluation_gate.py)
