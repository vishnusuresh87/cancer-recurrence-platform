# Cancer Recurrence Prediction Platform

A production-grade microservices platform for predicting cancer recurrence risk using a Random Survival Forest (RSF) machine learning model trained on SEER cancer registry data.

This repository supports both **Local Development** (Docker Compose, local PostgreSQL database, and React dev server) and **Cloud Deployment** (production-grade migration using GCP, GKE, Cloud SQL, and Artifact Registry).

---

## 📚 Table of Contents
1. [Architecture & Workflow](#architecture--workflow)
2. [Project Status](#project-status)
3. [Key Features](#key-features)
4. [Component Breakdown](#component-breakdown)
5. [Quick Start (Local Stack)](#quick-start-local-stack)
6. [Audits & Applied Fixes](#audits--applied-fixes)
7. [API Verification Example](#api-verification-example)
8. [Documentation Index](#documentation-index)

---

## 🏗️ Architecture & Workflow

### 1. Request Flow (real-time prediction)
```text
🌐 React UI Client (Port 3000)
             │
             ▼ HTTP (Port 8000)
┌─────────────────────────────────────────┐
│        BFF Service (API Gateway)        │
└────────────┬────────────────────────────┘
             ├────────────────────────────┐
             ▼ Proxy (Internal)           ▼ Proxy (Internal)
     ┌──────────────┐             ┌────────────────────────┐
     │ auth-service │             │   prediction-service   │
     │ (Port 8001)  │             │   (Port 8003)          │
     └──────────────┘             └───────────┬────────────┘
                                              │ Check updates
                                  ┌───────────▼────────────┐
                                  │model-management-service│
                                  │   (Port 8004)          │
                                  └───────────┬────────────┘
                                              │ Local disk
                                        ┌─────▼──────┐
                                        │ Model file │
                                        │ (.pkl)     │
                                        └────────────┘
```

### 2. Data Engineering & Training Pipeline
```text
seer_sample_200k.csv (Raw SEER Export)
         │
         ▼  load_raw_seer.py
   raw_seer (Table: 200k rows)       ← cancer-warehouse DB (Port 5433)
         │
         ▼  dbt run
   stg_seer_raw (View)               ← clean + type-safe columns
         │
         ▼ (Intermediate views)
   int_features & int_target         ← 28 engineered features + target
         │
         ▼
   fct_training_data_raw (Table)     ← raw string columns + target
         │
         ▼  retrain_from_dbt.py
   rsf_pipeline_v3.0.0.pkl           ← trained unified scikit-learn Pipeline
```

---

## 📊 Project Status

| Component | Status | Description |
| :--- | :--- | :--- |
| **`cancer-db` (PostgreSQL)** | Ready | relational database (port `55432`) containing baseline users, profiles, history, and model metadata. |
| **`cancer-cache` (Redis)** | Ready | Redis (port `6379`) used for token and active model caching. |
| **`cancer-warehouse` (Postgres)** | Ready | Analytics database (port `5433`) used to ingest raw data and run dbt pipelines. |
| **`dbt-transformations`** | Ready | dbt models mapping raw data to intermediate features and final marts. |
| **`auth-service`** | Ready | Internal JWT issuer, password hash (bcrypt), database schemas. |
| **`prediction-service`** | Ready | inference server executing models and supporting hot-swaps. |
| **`model-management-service`**| Ready | Tracks registered models, active tags, metrics, and paths. |
| **`bff-service`** | Ready | Central API Gateway running on public port `8000`. |
| **Frontend** | Ready | React SPA client dashboard running on public port `3000`. |

---

## ✨ Key Features

1.  **Unified ML Pipelines:** Prevention of train-serve skew by wrapping preprocessing steps (`SeerFeatureEngineer`, `ColumnTransformer`) and the estimator (`RandomSurvivalForest`) directly inside a unified scikit-learn `Pipeline`.
2.  **Zero-Downtime Hot-Reloading:** A background daemon thread inside the `prediction-service` polls the `model-management-service` every 6 hours and dynamically swaps the model in-memory without terminating active HTTP requests.
3.  **Encrypted Session Management:** Secure registration, login, and `/me` routes with JSON Web Tokens (JWT) signed by a server-side private key and managed via HttpOnly cookies.
4.  **Robust Preprocessing Fallbacks:** Graceful handling of missing optional parameters or demographic data during serving time by utilizing a Series fallback builder.

---

## 📁 Component Breakdown

*   [frontend/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/frontend): React application (Prediction Form, History, Profile details).
*   [services/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/services): Backend microservices (auth, BFF, prediction, model-management).
*   [shared/shared-transformers/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/shared/shared-transformers): Single source of truth containing clinical enums, validation constants, and pipeline transformers.
*   [dbt-transformations/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/dbt-transformations): Data transformation modeling directories.
*   [ml-pipeline/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/ml-pipeline): Model training code, data schemas, and pipeline metrics.
*   [scripts/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/scripts): SQL and Python initialization utilities.

---

## 🚀 Quick Start (Local Stack)

### Prerequisites
*   Docker Desktop (daemon running)
*   Python 3.10+
*   Node.js (v18+)

### 1. Start Services and Databases
```bash
# Clone the repository
git clone https://github.com/vishnusuresh87/cancer-recurrence-platform.git
cd cancer-recurrence-platform

# Spin up databases and Python microservices
docker compose up -d --build
```

### 2. Run the React Client
```bash
cd frontend
npm install
npm start
```
The client dashboard will compile and be available at **[http://localhost:3000](http://localhost:3000)**.

### 3. Run the Unit Test Suite
Verify features extraction and encoder transformations:
```bash
$env:PYTHONPATH="shared/shared-transformers"
.\.venv\bin\python -m pytest shared/shared-transformers/tests/
```

---

## 🛠️ Audits & Applied Fixes

We audited the codebase and resolved multiple bugs during local development:
*   **Startup Bug:** Fixed a `NameError` crash in the `prediction-service` root endpoint by elevating `model_loader` imports.
*   **Pipeline Support Mismatch:** Updated [predictor.py](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/services/prediction-service/app/inference/predictor.py) to check for unified `Pipeline` types, enabling support for both legacy estimators and new unified pipelines.
*   **Transformer Safety:** Added `_get_series` column fetcher in `SeerFeatureEngineer` to prevent `AttributeError` crashes when inputs lack optional fields.
*   **UI Mappings:** Updated `getRiskColor` in the History page to map `Moderate` and `Very High` levels to their respective orange/red warnings.
*   **SPA Transitions:** Converted auth link redirects to React Router `RouterLink` components to eliminate full-page browser reloads.
*   **Missing Pages:** Implemented a new Profile page to display patient registration metadata.

---

## 🔌 API Verification Example

Check API health directly via the BFF gateway:
```bash
# Verify Prediction Service health check proxy
curl http://localhost:8000/api/predict/health

# Response
# {"status":"healthy","service":"prediction-service","model_version":"rsf_seer_v1.0.0","model_status":"loaded"}
```

---

## 📄 Documentation Index

Explore detailed aspects of this project:
*   [local_plan.md](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/local_plan.md) — Tracks completed local environment steps, tests, and audited fixes.
*   [cloud_deployment.md](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/cloud_deployment.md) — Details the GCP-based production deployment plan using GKE, Cloud SQL, and Cloud Memorystore.
*   [documentation.md](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/documentation.md) — A comprehensive A-Z engineering report covering relational schemas, pipelines, and data flow.
