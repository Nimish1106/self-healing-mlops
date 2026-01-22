-- ============================================================
-- Phase 5: Production-Grade Storage Schema (CORRECTED)
-- ============================================================

DROP TABLE IF EXISTS model_versions CASCADE;
DROP TABLE IF EXISTS retraining_decisions CASCADE;
DROP TABLE IF EXISTS monitoring_metrics CASCADE;

-- ============================================================
-- A. Time-Series Monitoring Metrics
-- ============================================================
-- ✅ FIXED: Removed num_labeled, coverage_pct (asynchronous concern)
-- ✅ FIXED: Renamed drift_share → feature_drift_ratio (clarity)

CREATE TABLE monitoring_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL,

    -- Window context
    lookback_hours INT NOT NULL,
    num_predictions INT NOT NULL,

    -- Proxy metrics (flattened for fast queries)
    positive_rate FLOAT,
    probability_mean FLOAT,
    probability_std FLOAT,
    entropy FLOAT,

    -- Drift summary (dataset-level ONLY)
    dataset_drift_detected BOOLEAN DEFAULT FALSE,
    feature_drift_ratio FLOAT DEFAULT 0.0,  -- ✅ RENAMED (was drift_share)
    num_drifted_features INT DEFAULT 0,

    -- References to artifacts (NOT blobs)
    drift_summary_ref TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT monitoring_metrics_timestamp_unique UNIQUE (timestamp)
);

CREATE INDEX idx_monitoring_metrics_timestamp ON monitoring_metrics(timestamp DESC);
CREATE INDEX idx_monitoring_metrics_drift ON monitoring_metrics(dataset_drift_detected, feature_drift_ratio);

COMMENT ON COLUMN monitoring_metrics.feature_drift_ratio IS 'Fraction of features that drifted (e.g., 0.5 = 50% of features)';
COMMENT ON TABLE monitoring_metrics IS 'One row per monitoring run. Answers: Is system behavior changing?';

-- ============================================================
-- C. Retraining & Decision Log
-- ============================================================
-- ✅ FIXED: Removed gate_results JSONB (store in files)
-- ✅ FIXED: Changed trigger_reason enum (removed performance_degradation)
-- ✅ ADDED: labeled_samples, coverage_pct (belong here, not monitoring)

CREATE TABLE retraining_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL,

    -- Trigger context
    trigger_reason TEXT NOT NULL CHECK (
        trigger_reason IN ('scheduled', 'manual', 'drift_alert')  -- ✅ FIXED
    ),

    -- Drift context (snapshot at decision time)
    feature_drift_ratio FLOAT,  -- ✅ RENAMED (was drift_share)
    num_drifted_features INT,
    dataset_drift_detected BOOLEAN,
    drifted_features TEXT[],

    -- Data context (✅ MOVED HERE from monitoring_metrics)
    labeled_samples INT,
    coverage_pct FLOAT,

    -- Decision outcome
    action TEXT NOT NULL CHECK (
        action IN ('train', 'skip', 'promote', 'reject')
    ),

    -- Gate details (minimal, human-readable)
    failed_gate TEXT,
    reason TEXT,  -- ✅ gate_results JSONB removed, only human reason

    -- Model context
    shadow_model_version INT,
    production_model_version INT,

    -- Metrics (if promotion decision)
    f1_improvement_pct FLOAT,
    brier_change FLOAT,

    -- References to artifacts
    drift_summary_ref TEXT,
    evaluation_report_ref TEXT,  -- ✅ Detailed gate results stored here

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT retraining_decisions_timestamp_unique UNIQUE (timestamp)
);

CREATE INDEX idx_retraining_decisions_action ON retraining_decisions(action);
CREATE INDEX idx_retraining_decisions_trigger ON retraining_decisions(trigger_reason);
CREATE INDEX idx_retraining_decisions_drift ON retraining_decisions(dataset_drift_detected);

COMMENT ON TABLE retraining_decisions IS 'Audit trail. Answers: Why did we (or did not) take action?';
COMMENT ON COLUMN retraining_decisions.labeled_samples IS 'Number of labeled predictions at decision time';
COMMENT ON COLUMN retraining_decisions.coverage_pct IS 'Label coverage at decision time (asynchronous from monitoring)';

-- ============================================================
-- D. Model Lineage & Governance
-- ============================================================
-- ✅ ADDED: Partial unique index (only ONE model in Production)

CREATE TABLE model_versions (
    model_name TEXT NOT NULL,
    version INT NOT NULL,
    stage TEXT NOT NULL CHECK (
        stage IN ('Staging', 'Production', 'Archived', 'None')
    ),

    -- Lifecycle timestamps
    trained_at TIMESTAMP,
    promoted_at TIMESTAMP,
    archived_at TIMESTAMP,

    -- Training context
    trigger_reason TEXT,
    training_run_id TEXT,  -- MLflow run ID

    -- Performance snapshot
    f1_score FLOAT,
    brier_score FLOAT,
    num_samples INT,

    -- Drift context at training time
    feature_drift_ratio_at_training FLOAT,  -- ✅ RENAMED

    -- Decision reference
    decision_id UUID REFERENCES retraining_decisions(id),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (model_name, version)
);

CREATE INDEX idx_model_versions_stage ON model_versions(model_name, stage);
CREATE INDEX idx_model_versions_promoted ON model_versions(promoted_at DESC);

-- ✅ CRITICAL CONSTRAINT: Only ONE model can be in Production
CREATE UNIQUE INDEX one_production_model
ON model_versions(model_name)
WHERE stage = 'Production';

COMMENT ON INDEX one_production_model IS 'Governance invariant: exactly one production model per model_name';

-- ============================================================
-- Views for Common Queries
-- ============================================================

CREATE OR REPLACE VIEW v_recent_monitoring AS
SELECT
    timestamp,
    num_predictions,
    feature_drift_ratio,  -- ✅ RENAMED
    dataset_drift_detected,
    positive_rate,
    entropy
FROM monitoring_metrics
ORDER BY timestamp DESC
LIMIT 100;

CREATE OR REPLACE VIEW v_decision_history AS
SELECT
    d.timestamp,
    d.action,
    d.trigger_reason,
    d.feature_drift_ratio,  -- ✅ RENAMED
    d.labeled_samples,  -- ✅ Now in this table
    d.coverage_pct,     -- ✅ Now in this table
    d.failed_gate,
    d.reason,
    d.shadow_model_version,
    d.production_model_version
FROM retraining_decisions d
ORDER BY d.timestamp DESC;

CREATE OR REPLACE VIEW v_model_timeline AS
SELECT
    m.model_name,
    m.version,
    m.stage,
    m.trained_at,
    m.promoted_at,
    m.f1_score,
    d.feature_drift_ratio AS drift_at_training,  -- ✅ RENAMED
    d.action
FROM model_versions m
LEFT JOIN retraining_decisions d ON m.decision_id = d.id
ORDER BY m.version DESC;

-- ============================================================
-- Retention Policy Function
-- ============================================================

CREATE OR REPLACE FUNCTION cleanup_old_monitoring_metrics()
RETURNS void AS $$
BEGIN
    -- Keep only last 90 days of monitoring metrics
    DELETE FROM monitoring_metrics
    WHERE timestamp < NOW() - INTERVAL '90 days';

    RAISE NOTICE 'Cleaned up monitoring metrics older than 90 days';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_monitoring_metrics IS 'Run monthly: SELECT cleanup_old_monitoring_metrics();';
