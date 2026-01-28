# Self-Healing MLOps Pipeline - Architecture

## High-Level System Architecture

```mermaid
graph TB
    subgraph "Data Ingestion"
        A[User Requests] --> B[FastAPI Service]
    end

    subgraph "Prediction Layer"
        B --> C[Production Model]
        C --> D[Prediction Logger]
        D --> E[(Predictions CSV)]
    end

    subgraph "Monitoring Layer - Phase 3"
        F[Monitoring Scheduler] --> G[Load Predictions]
        G --> H{Sufficient Samples?}
        H -->|No| I[Wait]
        H -->|Yes| J[Proxy Metrics]
        H -->|Yes| K[Drift Detection]
        J --> L[Results Storage]
        K --> L
    end

    subgraph "Retraining Layer - Phase 4"
        M[Retraining Trigger] --> N{Drift Significant?}
        N -->|Yes| O[Train Shadow Model]
        O --> P[Evaluation Gate]
        P --> Q{All Gates Pass?}
        Q -->|Yes| R[Promote to Production]
        Q -->|No| S[Archive & Log]
    end

    subgraph "Storage Layer"
        T[(Reference Data)]
        U[(MLflow Registry)]
        V[(Labels Store)]
    end

    E -.-> G
    L -.-> M
    T -.-> K
    V -.-> O
    R --> U

    style B fill:#4CAF50
    style C fill:#2196F3
    style F fill:#FF9800
    style O fill:#9C27B0
    style P fill:#F44336
```

## Phase-by-Phase Flow

### Phase 1-2: Foundation
```mermaid
graph LR
    A[Training Data] --> B[Model Training]
    B --> C[MLflow Registry]
    C --> D[Production Model]
    D --> E[FastAPI Service]
    E --> F[User Predictions]
```

### Phase 3: Monitoring
```mermaid
graph TD
    A[Predictions] --> B[Prediction Logger]
    B --> C{Sample Count ≥ 200?}
    C -->|No| D[Wait for Data]
    C -->|Yes| E[Compute Proxy Metrics]
    C -->|Yes| F[Detect Drift]
    E --> G[Log Results]
    F --> G
    G --> H[MLflow + JSON]

    I[Reference Data] -.-> F
```

### Phase 4: Self-Healing
```mermaid
flowchart TD
    A[Triggers<br/>• Scheduled<br/>• Drift Observed<br/>• Manual] --> B[Check Retraining Conditions]

    B --> C{Sufficient Labeled Data<br/>+ Coverage?}
    C -- No --> Z[Skip Retraining<br/>Log Decision]

    C -- Yes --> D[Train Shadow Model<br/>Temporal Split]

    D --> E{Training Aborted?}
    E -- Yes --> Z
    E -- No --> F[Replay-Based Evaluation<br/>Prod vs Shadow]

    F --> G{First Deployment?}
    G -- Yes --> K[Auto-Promote]

    G -- No --> H[Evaluation Gate<br/>Multi-Criteria]

    H --> I{Gate Passed?}
    I -- Yes --> K[Promote to Production]
    I -- No --> J[Reject Shadow Model]

    K --> L[Log Promotion]
    J --> L
    Z --> L

```

## Component Interactions

### Prediction Flow
```mermaid
sequenceDiagram
    participant User
    participant API
    participant Model
    participant Logger
    participant Storage

    User->>API: POST /predict
    API->>Model: get_prediction(features)
    Model-->>API: prediction, probability
    API->>Logger: log_prediction()
    Logger->>Storage: append to CSV
    API-->>User: prediction response
```

### Monitoring Flow
```mermaid
sequenceDiagram
    participant Scheduler
    participant MonitoringJob
    participant Storage
    participant Analytics
    participant MLflow

    Scheduler->>MonitoringJob: trigger (every 5min)
    MonitoringJob->>Storage: load_predictions(24h)
    Storage-->>MonitoringJob: predictions_df

    MonitoringJob->>MonitoringJob: check sample count

    alt Sufficient samples
        MonitoringJob->>Analytics: compute_proxy_metrics()
        Analytics-->>MonitoringJob: metrics

        MonitoringJob->>Analytics: detect_drift()
        Analytics-->>MonitoringJob: drift_results

        MonitoringJob->>MLflow: log_results()
        MonitoringJob->>Storage: save_json()
    else Insufficient samples
        MonitoringJob->>MonitoringJob: skip analysis
    end
```

### Retraining Flow
```mermaid
sequenceDiagram
    participant Trigger
    participant Trainer
    participant EvalGate
    participant MLflow
    participant Production

    Trigger->>Trainer: retrain_needed()
    Trainer->>Trainer: train_shadow_model()
    Trainer->>MLflow: log to Staging

    Trainer->>EvalGate: evaluate(prod, shadow)

    EvalGate->>EvalGate: check_all_gates()

    alt All gates pass
        EvalGate->>MLflow: promote to Production
        MLflow->>Production: update model
        EvalGate-->>Trigger: success
    else Any gate fails
        EvalGate->>MLflow: archive shadow
        EvalGate-->>Trigger: rejected (reason)
    end
```

## Data Flow

### Prediction Data Flow
```mermaid
graph LR
    A[Input Features] --> B[API Validation]
    B --> C[Model Inference]
    C --> D[Prediction + Probability]
    D --> E[Response to User]
    D --> F[Prediction Logger]
    F --> G[predictions.csv]

    style B fill:#FFC107
    style G fill:#03A9F4
```

### Label Data Flow (Delayed)
```mermaid
graph TD
    A[Day 1: Prediction Made] --> B[prediction_id created]
    B --> C[Logged to predictions.csv]

    D[Day 180: Label Arrives] --> E[Match by prediction_id]
    E --> F[Label Store]
    F --> G[Enable True Evaluation]

    C -.->|waiting| E

    style A fill:#4CAF50
    style D fill:#FF9800
```

## Storage Architecture

```mermaid
graph TB
    subgraph "File Storage"
        A[predictions.csv<br/>Append-only]
        B[reference_data.csv<br/>IMMUTABLE]
        C[labels.csv<br/>Append-only]
    end

    subgraph "MLflow Storage"
        D[Experiments]
        E[Model Registry]
        F[Artifacts]
    end

    subgraph "Monitoring Storage"
        G[monitoring_results/]
        H[drift_reports/]
    end

    I[API] --> A
    J[Bootstrap Script] --> B
    K[Label Collector] --> C

    L[Training] --> D
    L --> E
    L --> F

    M[Monitoring Job] --> G
    M --> H

    style B fill:#F44336
    style A fill:#4CAF50
    style E fill:#2196F3
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Compose Stack"
        A[MLflow Server<br/>Port 5000]
        B[API Service<br/>Port 8000]
        C[Monitoring Scheduler]
        D[Airflow<br/>Port 8080]
    end

    subgraph "Shared Volumes"
        E[mlflow/]
        F[monitoring/]
        G[data/]
    end

    A --- E
    B --- E
    B --- F
    C --- F
    D --- E

    H[User Requests] --> B

    style A fill:#FF9800
    style B fill:#4CAF50
    style C fill:#2196F3
    style D fill:#9C27B0
```

## Key Design Decisions

### 1. Append-Only Predictions
- **Why:** Immutable audit trail
- **Benefits:** No data loss, replay capability
- **Tradeoff:** Storage grows over time

### 2. Frozen Reference Data
- **Why:** Statistical validity
- **Benefits:** Comparable drift detection
- **Tradeoff:** Manual updates only

### 3. Delayed Labels
- **Why:** Real-world constraint
- **Benefits:** Realistic evaluation gate
- **Tradeoff:** Can't evaluate immediately

### 4. Shadow Model Validation
- **Why:** Safe deployment
- **Benefits:** No production degradation
- **Tradeoff:** Higher infrastructure cost

### 5. Multi-Criteria Gates
- **Why:** Comprehensive evaluation
- **Benefits:** Prevents false promotions
- **Tradeoff:** Complex logic

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API** | FastAPI | High-performance predictions |
| **Model Tracking** | MLflow | Experiment + registry |
| **Drift Detection** | Evidently AI | Statistical monitoring |
| **Data Validation** | Pandera | Schema enforcement |
| **Testing** | pytest | Comprehensive tests |
| **Orchestration** | Airflow | DAG workflows |
| **Containerization** | Docker | Environment consistency |
| **CI/CD** | GitHub Actions | Automated testing |

## Scalability Considerations

### Current Architecture (Single Server)
- ✅ Suitable for < 10k predictions/day
- ✅ Development and testing
- ✅ Monitoring <24 hours history

### Future Scaling (Recommended)
- 📊 Database (PostgreSQL) instead of CSV
- 🔄 Kafka for prediction streaming
- ☁️ Cloud storage (S3) for artifacts
- 📈 Kubernetes for orchestration
- 🗄️ Feature store integration
