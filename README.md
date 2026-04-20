# Cancer Recurrence Prediction Platform

A production-grade microservices platform for predicting cancer recurrence risk using a Random Survival Forest (RSF) model trained on SEER data.

## Project Status

| Component | Status |
|---|---|
| PostgreSQL + Redis (Docker) | ✅ Running |
| SEER data loading (`load_raw_seer.py`) | ✅ 200,000 rows loaded |
| dbt data warehouse (`seer_warehouse`) | ✅ 119,990 rows in `fct_training_data` |
| ML training pipeline (`retrain_from_dbt.py`) | ✅ RSF v2.0.0 trained successfully |
| `auth-service` (port 8001) | ✅ Implemented |
| `feature-service` (port 8002) | ✅ Implemented |
| `prediction-service` (port 8003) | ✅ Implemented |
| `model-management-service` (port 8004) | ✅ Implemented |
| Frontend | 🔄 In progress |

---

## Architecture

```text
┌─────────────────────────────────────────────────────┐
│                    Client / Frontend                │
└───────────┬─────────────────────────────────────────┘
            │
┌───────────▼─────────────────────────────────────────┐
│              API Gateway (planned: Kong)             │
└───┬───────────┬───────────┬──────────────┬──────────┘
    │           │           │              │
┌───▼───┐  ┌───▼───┐  ┌────▼────┐  ┌─────▼──────┐
│ Auth  │  │Feature│  │Predict  │  │  Model     │
│:8001  │  │:8002  │  │:8003    │  │  Mgmt:8004 │
└───────┘  └───────┘  └────┬────┘  └────────────┘
                            │
                    ┌───────▼───────┐
                    │  RSF Model    │
                    │  (.pkl file)  │
                    └───────────────┘
```

### Data Pipeline

```text
seer_sample_200k.csv
        │
        ▼  load_raw_seer.py
  raw_seer (200k rows)          ← cancer-warehouse DB (port 5433)
        │
        ▼  dbt run
  stg_seer_raw (VIEW)           ← clean + type-safe SEER columns
        │
        ▼  (ephemeral)
  int_features                  ← 28 engineered ML features
  int_recurrence_target         ← recurrence target variable
        │
        ▼  (TABLE)
  fct_training_data (~120k rows) ← ML-ready: 28 features + target
        │
        ▼  retrain_from_dbt.py
  rsf_seer_v2.0.0.pkl           ← trained RSF model
```

---

## Services

| Service | Port | Responsibility |
|---|---|---|
| `auth-service` | 8001 | JWT authentication & user management |
| `feature-service` | 8002 | Raw patient data → 28-feature vector (inference time) |
| `prediction-service` | 8003 | Feature vector → survival probability |
| `model-management-service` | 8004 | Model versioning, promote, rollback |

---

## Quick Start

### Prerequisites
- Docker Desktop (with the Docker daemon running)
- Python 3.10+ and WSL2 (Ubuntu) for running scripts
- dbt-postgres (`pip install dbt-postgres`)

### 1. Clone and start the stack
```bash
git clone https://github.com/vishnusuresh87/cancer-recurrence-platform.git
cd cancer-recurrence-platform
docker-compose up -d
```

### 2. Load SEER data into the warehouse
```bash
cd scripts
pip install pandas psycopg2-binary sqlalchemy
python load_raw_seer.py
# ✅ Loaded 200,000 rows to raw_seer table
```

### 3. Run dbt transformations
```bash
cd dbt-transformations/seer_warehouse
pip install dbt-postgres
dbt run
# ✅ fct_training_data: ~120,000 rows
```

### 4. Train the model
```bash
cd ml-pipeline/scripts
pip install scikit-survival scikit-learn sqlalchemy joblib pandas numpy
python retrain_from_dbt.py
# ✅ Model saved: rsf_seer_v2.0.0.pkl
```

### 5. Verify services
| URL | Description |
|---|---|
| http://localhost:8001/docs | Auth Service API docs |
| http://localhost:8002/docs | Feature Service API docs |
| http://localhost:8003/docs | Prediction Service API docs |
| http://localhost:8004/docs | Model Management API docs |

---

## Project Structure

```text
cancer-recurrence-platform/
├── docker-compose.yml              # Full local stack (2 PostgreSQL DBs + Redis)
├── services/
│   ├── auth-service/               # FastAPI — JWT auth (port 8001)
│   ├── feature-service/            # FastAPI — feature engineering (port 8002)
│   ├── prediction-service/         # FastAPI — RSF inference (port 8003)
│   └── model-management-service/   # FastAPI — model lifecycle (port 8004)
├── ml-pipeline/
│   ├── scripts/
│   │   └── retrain_from_dbt.py     # Train RSF from fct_training_data
│   ├── notebooks/                  # EDA & experiments
│   └── models/                     # Trained model files (gitignored)
├── dbt-transformations/
│   └── seer_warehouse/
│       ├── models/
│       │   ├── example/staging/    # stg_seer_raw (view)
│       │   ├── intermediate/       # int_features, int_recurrence_target (ephemeral)
│       │   └── marts/              # fct_training_data (table, ~120k rows)
│       └── dbt_project.yml
├── scripts/
│   ├── load_raw_seer.py            # Load CSV → raw_seer (PostgreSQL)
│   ├── init_db.sql                 # PostgreSQL schema (cancer-db)
│   └── create_model_versions_table.sql
└── shared/
    ├── shared-schemas/             # Pydantic schemas shared across services
    └── shared-utils/               # Common utilities
```

---

## ML Model

- **Algorithm**: Random Survival Forest (`scikit-survival`)
- **Dataset**: SEER (Surveillance, Epidemiology, and End Results) — 200k patients
- **Training data**: ~120k first-primary malignant cases from `fct_training_data`
- **Target**: `recurred` (binary) + `time_to_recurrence_months` (survival time)
- **Features**: 28 engineered features (age, stage, grade, treatment, node ratio, receptor subtype, etc.)
- **Version**: `rsf_seer_v2.0.0` — trained from dbt-transformed warehouse data

---

## API Usage Example

```bash
# 1. Transform raw patient data into a feature vector
curl -X POST http://localhost:8002/api/v1/transform \
  -H "Content-Type: application/json" \
  -d '{
    "age_group": "50-54 years",
    "cancer_site": "Breast",
    "harmonized_stage": "Localized",
    "tumor_grade": "Grade II",
    "surgery_performed": true,
    "chemotherapy": true,
    ...
  }'

# 2. Run prediction with the feature vector
curl -X POST http://localhost:8003/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [...], "time_horizon": 60}'
```

---

## Tech Stack

- **API Framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL 15 — `cancer-db` (app data, port 55432) + `seer-warehouse` (ML data, port 5433)
- **Cache**: Redis 7 (port 6379)
- **Data Warehouse / ETL**: dbt-postgres (`seer_warehouse` project)
- **ML**: scikit-survival, scikit-learn, pandas, numpy
- **Containerisation**: Docker + Docker Compose
- **Runtime**: Python 3.12, WSL2 (Ubuntu)
