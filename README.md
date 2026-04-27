# Cancer Recurrence Prediction Platform

A production-grade microservices platform for predicting cancer recurrence risk using a Random Survival Forest (RSF) model trained on SEER data.

## Project Status

| Component | Status |
|---|---|
| PostgreSQL + Redis (Docker) | Running |
| SEER data loading (`load_raw_seer.py`) | 200,000 rows loaded |
| dbt data warehouse (`seer_warehouse`) | 119,990 rows in `fct_training_data` |
| ML training pipeline (`retrain_from_dbt.py`) | RSF v1.0.0 trained successfully |
| `bff-service` (port 8000) | Implemented (API Gateway) |
| `auth-service` (Internal) | Implemented (JWT Auth) |
| `prediction-service` (Internal) | Implemented (Feature processing + RSF Inference) |
| `model-management-service` (Internal) | Implemented (Model lifecycle & hot-reloading) |
| Frontend (port 3000) | Implemented (React, Material-UI, Prediction History) |

---

## Architecture

```text
┌─────────────────────────────────────────────────────┐
│                    Client / Frontend                │
│                 (React / Material-UI)               │
└───────────┬─────────────────────────────────────────┘
            │ HTTP (port 3000)
┌───────────▼─────────────────────────────────────────┐
│              BFF Service (API Gateway)              │
│                     (port 8000)                     │
└───┬─────────────────────────┬───────────────────────┘
    │ Proxy                   │ Proxy
┌───▼───┐                 ┌───▼──────────┐       ┌──────────────┐
│ Auth  │                 │ Prediction   │◄──────┤ Model Mgmt   │
│Service│                 │ Service      │ Polls │ Service      │
└───────┘                 └────┬─────────┘       └──────────────┘
                               │
                       ┌───────▼───────┐
                       │  RSF Model    │
                       │  (In-Memory)  │
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
  rsf_seer_v1.pkl               ← trained RSF model
```

---

## Key Features & Functionalities

### 1. Robust Machine Learning Inference
- **Algorithm**: Random Survival Forest (`scikit-survival`) trained on real SEER data.
- **Inference Engine**: Translates complex clinical inputs (like broad histology categories) into strict ICD-O-3 numeric representations and processes 28 engineered features on the fly.
- **Explainability**: Generates dynamic risk levels, interpretation text, and a time-horizon survival curve.

### 2. Microservices Architecture
- **BFF (Backend-For-Frontend)**: Centralized API gateway managing CORS and proxying requests to private microservices.
- **Private Networking**: Core services (`auth`, `prediction`, `model-management`) are shielded from public access, communicating via internal Docker networking.

### 3. Automated Model Lifecycle Management
- **Zero-Downtime Swaps**: The `prediction-service` runs a background thread that polls the `model-management-service` every 6 hours. If a new production model is detected, it is hot-reloaded into memory without dropping requests.
- **Redis Caching**: The active model pipeline is cached in Redis to accelerate load times across distributed worker nodes.

### 4. Strict Type Safety & Validation
- **Shared Pydantic Schemas**: A `shared-transformers` directory acts as a single source of truth for Enums and API contracts, ensuring the frontend, BFF, and prediction services are strictly synchronized.

### 5. Data Engineering & Analytics Engineering (dbt)
- **dbt (data build tool)**: The entire ML data pipeline is built using dbt (`dbt-postgres`). It serves as the bridge between raw data and the ML model.
- **Data Quality & Testing**: Enforces constraints, not-null checks, and accepted values directly on the `cancer-warehouse` database before any model training occurs.
- **Modular Transformations**: Uses a layered architecture (Staging → Intermediate → Marts) using ephemeral models to calculate node ratios, harmonize staging, and generate the final `fct_training_data` table efficiently.

### 6. Production-Ready Frontend
- Developed using **React** and **Material-UI**.
- Features an intuitive **Prediction Form** with clinical constraints (e.g., locking breast-cancer-specific biomarkers when inapplicable).
- Includes a persistent **Prediction History** dashboard linked to the user's account.

---

## Detailed Component Breakdown & Inner Workings

### 1. Frontend (React + Material-UI)
- **Role:** The user-facing application where clinicians or patients input clinical data to receive a recurrence prediction. Exposes port 3000.
- **Inner Workings:** It provides a dynamic form that ensures only valid combinations of data can be submitted (e.g., locking breast-cancer-specific biomarkers when the cancer site is not breast). It communicates exclusively with the `bff-service` to authenticate users and fetch predictions. It also includes a dashboard to view past prediction history.

### 2. BFF Service (Backend-For-Frontend / API Gateway)
- **Role:** Acts as the single public entry point (Port 8000) for the Frontend to interact with the backend infrastructure.
- **Inner Workings:** Built with FastAPI, it acts as a reverse proxy routing requests to the isolated internal microservices (`auth-service` and `prediction-service`). It handles Cross-Origin Resource Sharing (CORS) and ensures that internal service ports and IPs are never exposed to the public internet, adding a critical layer of security.

### 3. Prediction Service
- **Role:** The core ML inference engine of the platform. Runs on an internal Docker network.
- **Inner Workings:** 
  - **Feature Processing:** When it receives raw clinical data, it utilizes a `FeatureProcessor` to map human-readable inputs (like "Ductal carcinoma") into strict numeric representations (like ICD-O-3 code `8500.0`) that the model was trained on. It calculates complex features like `node_ratio` and `treatment_intensity` on the fly.
  - **Inference:** It runs the processed 28-feature vector through the loaded Random Survival Forest (RSF) model to compute a survival curve and a specific recurrence probability for a given time horizon.
  - **Persistence:** It saves the raw inputs, the generated prediction, and the model version used to the PostgreSQL database for historical tracking.
  - **Hot-Reloading:** It runs a background polling thread that checks the `model-management-service` every 6 hours. If a new model version is detected, it hot-reloads the new `.pkl` model into memory without dropping any active requests.

### 4. Model Management Service
- **Role:** The control plane for the machine learning model lifecycle. Runs on an internal Docker network.
- **Inner Workings:** It tracks all trained model versions in the PostgreSQL database. When data scientists train a new model (e.g., `rsf_seer_v2.0.0`), it is registered here. This service exposes an API that the `prediction-service` calls to discover the exact file path of the currently active "Production" model, enabling automated zero-downtime model swaps.

### 5. Auth Service
- **Role:** Manages user identity and security. Runs on an internal Docker network.
- **Inner Workings:** It handles user registration, login, and issues JSON Web Tokens (JWT). These tokens are required to access the prediction endpoints via the BFF. It stores encrypted user credentials securely in the PostgreSQL database.

### 6. Data Engineering & Analytics (dbt + cancer-warehouse)
- **Role:** Transforms raw SEER dataset exports into clean, ML-ready training data. Exposes port 5433 for data scientist access.
- **Inner Workings:** Raw CSV data is loaded into the `cancer-warehouse` (a dedicated PostgreSQL instance). `dbt` (data build tool) then runs a series of SQL-based transformations. It enforces strict data quality tests (not-null, accepted values), creates ephemeral intermediate views to calculate features, and finally materializes a pristine `fct_training_data` table containing ~120,000 rows. The Python ML pipeline then reads directly from this table to train the RSF model.

### 7. Redis Cache
- **Role:** High-speed in-memory caching layer. Runs on an internal Docker network.
- **Inner Workings:** Once the `prediction-service` loads the heavy (~350MB) model `.pkl` file from disk, it serializes the loaded pipeline into Redis (with a 24-hour TTL). If multiple instances of the `prediction-service` are spun up to horizontally scale and handle high traffic, the worker nodes bypass the slow disk read and fetch the active model instantly from Redis.

### 8. PostgreSQL (cancer-db)
- **Role:** The primary transactional database for the application. Exposes port 55432.
- **Inner Workings:** It stores structured relational data across several domains: User accounts and hashed passwords for the `auth-service`, prediction history logs for the `prediction-service`, and model version metadata for the `model-management-service`.

---

## Quick Start

### Prerequisites
- Docker Desktop (with the Docker daemon running and WSL2 integration enabled)
- Python 3.10+ and WSL2 (Ubuntu) for running scripts
- `dbt-postgres` (`pip install dbt-postgres`)
- Node.js (v18+)

### 1. Clone and start the stack
```bash
git clone https://github.com/vishnusuresh87/cancer-recurrence-platform.git
cd cancer-recurrence-platform
docker compose up -d --build
```

### 2. Start the Frontend
```bash
cd frontend
npm install
npm start
```
The app will be available at `http://localhost:3000`.

### 3. Load SEER data into the warehouse (Optional - For Retraining)
```bash
cd scripts
pip install pandas psycopg2-binary sqlalchemy
python load_raw_seer.py
# Loaded 200,000 rows to raw_seer table
```

### 4. Run dbt transformations (Optional - For Retraining)
```bash
cd dbt-transformations/seer_warehouse
pip install dbt-postgres
dbt run
# fct_training_data: ~120,000 rows
```

### 5. Train the model (Optional - For Retraining)
```bash
cd ml-pipeline/scripts
pip install scikit-survival scikit-learn sqlalchemy joblib pandas numpy
python retrain_from_dbt.py
# Model saved: rsf_seer_v1.pkl
```

---

## API Usage Example via BFF

```bash
# Run prediction with raw clinical features through the BFF Gateway
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -d '{
    "age_group": "50-54 years",
    "cancer_site": "Breast",
    "harmonized_stage": "Localized",
    "tumor_grade": "Grade II",
    "histology_broad": "Ductal carcinoma",
    "tumor_size_mm": 20,
    "nodes_examined": 10,
    "nodes_positive": 2,
    "surgery_performed": true,
    "chemotherapy": true,
    "radiation_type": "None",
    "surgery_radiation_sequence": "Surgery before radiation",
    "days_to_treatment": "0-30 days",
    "mets_bone": false,
    "mets_liver": false,
    "mets_lung": false,
    "mets_brain": false,
    "lvi": "Absent",
    "er_status": "Positive",
    "pr_status": "Positive",
    "her2_status": "Negative",
    "marital_status": "Married",
    "income_level": "Medium",
    "rural_urban": "Urban",
    "laterality": "Left",
    "sex": "Female",
    "query_years": 5
  }'
```

---

## Tech Stack

- **Frontend**: React, Material-UI, Axios
- **API Framework**: FastAPI + Uvicorn
- **Data Warehouse / ETL**: **dbt** (data build tool) via `dbt-postgres` (`seer_warehouse` project)
- **Database**: PostgreSQL 15 — `cancer-db` (app data) + `cancer-warehouse` (dbt/ML training data)
- **Cache**: Redis 7
- **ML**: scikit-survival, scikit-learn, pandas, numpy
- **Containerisation**: Docker + Docker Compose V2
- **Runtime**: Python 3.12, Node.js, WSL2 (Ubuntu)
