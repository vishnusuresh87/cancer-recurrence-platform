# Cancer Recurrence Prediction Platform

A production-grade microservices platform for predicting cancer recurrence risk using a Random Survival Forest (RSF) model trained on SEER data.

## Architecture

```
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

## Services

| Service | Port | Responsibility |
|---|---|---|
| `auth-service` | 8001 | JWT authentication & user management |
| `feature-service` | 8002 | Raw patient data → 28-feature vector |
| `prediction-service` | 8003 | Feature vector → survival probability |
| `model-management-service` | 8004 | Model versioning, promote, rollback |

## Quick Start

### Prerequisites
- Docker Desktop
- Python 3.10+

### 1. Clone and configure
```bash
git clone https://github.com/YOUR_USERNAME/cancer-recurrence-platform.git
cd cancer-recurrence-platform

# Copy and fill in env vars for each service
cp services/auth-service/.env.example services/auth-service/.env
```

### 2. Start the full stack
```bash
docker-compose up --build
```

### 3. Verify services
| URL | Description |
|---|---|
| http://localhost:8001/docs | Auth Service API docs |
| http://localhost:8002/docs | Feature Service API docs |
| http://localhost:8003/docs | Prediction Service API docs |
| http://localhost:8004/docs | Model Management API docs |

## Project Structure

```
cancer-recurrence-platform/
├── docker-compose.yml              # Full local stack
├── services/
│   ├── auth-service/               # FastAPI — JWT auth
│   ├── feature-service/            # FastAPI — feature engineering
│   ├── prediction-service/         # FastAPI — RSF inference
│   └── model-management-service/   # FastAPI — model lifecycle
├── ml-pipeline/
│   ├── scripts/                    # Training scripts
│   ├── notebooks/                  # EDA & experiments
│   └── models/                     # Trained model files (gitignored)
├── shared/
│   ├── shared-schemas/             # Pydantic schemas shared across services
│   ├── shared-transformers/        # Feature encoding helpers
│   └── shared-utils/               # Common utilities
├── scripts/
│   ├── init_db.sql                 # PostgreSQL schema setup
│   └── create_model_versions_table.sql
└── dbt-transformations/            # SEER data warehouse transforms
```

## ML Model

- **Algorithm**: Random Survival Forest (`scikit-survival`)
- **Dataset**: SEER (Surveillance, Epidemiology, and End Results)
- **Target**: Cancer recurrence probability at a given time horizon
- **Features**: 28 engineered features (age group, stage, grade, treatment, node ratio, etc.)
- **Metrics**: C-index ~0.78, Brier score ~0.12

## API Usage Example

```bash
# 1. Get a feature vector from raw patient data
curl -X POST http://localhost:8002/api/v1/transform \
  -H "Content-Type: application/json" \
  -d '{"age_group": "50-59", "stage": "II", "grade": "3", ...}'

# 2. Run prediction with that feature vector
curl -X POST http://localhost:8003/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [...], "time_horizon": 60}'
```

## Tech Stack

- **API Framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL 15 (async via asyncpg + SQLAlchemy 2.0)
- **Cache**: Redis 7
- **ML**: scikit-survival, scikit-learn, pandas, numpy
- **Containerisation**: Docker + Docker Compose
- **Data Warehouse**: PostgreSQL (local), planned: BigQuery / DuckDB
