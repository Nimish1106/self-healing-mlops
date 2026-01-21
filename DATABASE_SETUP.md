# Database Initialization Guide

## Overview
The MLOps system uses PostgreSQL to track model versions, monitoring metrics, and retraining decisions. This guide covers database setup and initialization.

## Database Architecture

### Database
- **Name**: `mlops`
- **Host**: `postgres` (Airflow's PostgreSQL service)
- **Port**: 5432
- **User**: `airflow`
- **Owner**: `airflow`

### Tables (3 Main)
1. **model_versions**
   - Tracks production and candidate model versions
   - Stores MLflow run IDs and model staging state
   - Records model performance metrics

2. **monitoring_metrics**
   - Stores drift detection results
   - Records proxy metrics (coverage, data patterns)
   - Tracks data quality metrics

3. **retraining_decisions**
   - Logs evaluation gate decisions
   - Records which gate(s) failed or passed
   - Tracks promotion/rejection reasons

### Views (3 Analytical)
1. **v_decision_history**
   - Timeline of all promotion decisions
   - Easy query: recent decisions with model info

2. **v_model_timeline**
   - Model version progression over time
   - Tracks which version is in production
   - Shows when each version was deployed

3. **v_recent_monitoring**
   - Latest monitoring results grouped by metric type
   - Most recent drift reports
   - Current system health snapshot

## Setup Steps

### Step 1: Create Database
```bash
# First, create the 'mlops' database
docker-compose exec -T api python scripts/db/create_database.py

# Expected output:
# Creating database 'mlops'...
# ✅ Database 'mlops' created successfully
```

**What this does**:
- Connects to PostgreSQL as `airflow` user
- Creates new database `mlops` if it doesn't exist
- Sets `airflow` as owner

### Step 2: Initialize Schema
```bash
# Then, create tables and views
docker-compose exec -T api python scripts/db/init_database.py

# Expected output:
# ✅ Database initialized successfully
# Created 6 tables:
#   - model_versions
#   - monitoring_metrics
#   - retraining_decisions
#   - v_decision_history
#   - v_model_timeline
#   - v_recent_monitoring
```

**What this does**:
- Executes `/app/scripts/db/schema.sql`
- Creates 3 main tables
- Creates 3 analytical views

### Step 3: Verify Setup
```bash
# Check tables exist
docker-compose exec -T postgres psql -U airflow -d mlops -c "\dt"

# Expected output:
# List of relations
#  Schema |         Name         | Type  |  Owner
# --------+----------------------+-------+---------
#  public | model_versions       | table | airflow
#  public | monitoring_metrics   | table | airflow
#  public | retraining_decisions | table | airflow
```

## Schema Details

### model_versions
```sql
CREATE TABLE model_versions (
    id SERIAL PRIMARY KEY,
    mlflow_run_id VARCHAR(255) UNIQUE NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    status VARCHAR(50),  -- 'staging', 'production', 'archived'
    f1_score FLOAT,
    brier_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    promoted_at TIMESTAMP
);
```

### monitoring_metrics
```sql
CREATE TABLE monitoring_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metric_type VARCHAR(100),  -- 'drift', 'coverage', 'performance'
    metric_name VARCHAR(255),
    metric_value FLOAT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### retraining_decisions
```sql
CREATE TABLE retraining_decisions (
    id SERIAL PRIMARY KEY,
    decision_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(50),  -- 'promote', 'reject', 'pending'
    candidate_mlflow_run_id VARCHAR(255),
    gate_results JSONB,  -- All 6 gate results as JSON
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Common Queries

### List all production models
```sql
SELECT * FROM model_versions 
WHERE status = 'production' 
ORDER BY promoted_at DESC;
```

### View recent decisions
```sql
SELECT * FROM v_decision_history 
LIMIT 10;
```

### Check latest monitoring metrics
```sql
SELECT * FROM v_recent_monitoring 
LIMIT 20;
```

### Get model promotion timeline
```sql
SELECT * FROM v_model_timeline 
ORDER BY created_at DESC;
```

## Troubleshooting

### Error: database "mlops" does not exist
**Solution**: Run `create_database.py` first
```bash
docker-compose exec -T api python scripts/db/create_database.py
```

### Error: relation "model_versions" does not exist
**Solution**: Run `init_database.py` after database is created
```bash
docker-compose exec -T api python scripts/db/init_database.py
```

### Cannot connect to PostgreSQL
**Check**:
1. PostgreSQL service is running: `docker-compose ps postgres`
2. Credentials are correct in environment or db_manager.py
3. Network connectivity between containers

### Reset Database (Development Only)
```bash
# Drop and recreate everything
docker-compose exec -T postgres psql -U airflow -d postgres -c "DROP DATABASE mlops;"
docker-compose exec -T api python scripts/db/create_database.py
docker-compose exec -T api python scripts/db/init_database.py
```

## Environment Variables

Set these to override defaults:

```bash
POSTGRES_HOST=postgres          # PostgreSQL hostname
POSTGRES_PORT=5432            # PostgreSQL port
POSTGRES_USER=airflow         # Database user
POSTGRES_PASSWORD=airflow     # Database password
MLOPS_DB_NAME=mlops           # MLOps database name
```

## Files

- `scripts/db/create_database.py` - Creates `mlops` database
- `scripts/db/init_database.py` - Initializes schema
- `scripts/db/schema.sql` - Table and view definitions
- `src/storage/db_manager.py` - Connection pooling and utilities

## Notes

- Database is separate from Airflow's own database
- Uses connection pooling for efficiency
- JSONB columns for flexible metadata storage
- Views provide clean query interfaces for analytics
- All timestamps in UTC

---

**Status**: ✅ Database fully initialized and ready for use

Run monitoring and retraining jobs - they will automatically log decisions to these tables!
