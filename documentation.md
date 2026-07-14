# Cancer Recurrence Platform — Comprehensive Project Documentation

A comprehensive guide and technical report covering the design, implementation, and deployment of the Cancer Recurrence Prediction Platform.

---

## 📖 1. Project Overview & Objectives

### The Objective
The goal of this platform is to provide clinicians and cancer survivors with an evidence-based prediction of cancer recurrence probability (e.g. over a 5-year or 10-year horizon) using patient clinical history. 

### Key Objectives
*   **Predictive Accuracy:** Train machine learning models using the **SEER (Surveillance, Epidemiology, and End Results)** cancer registry dataset (comprising millions of historical patient records).
*   **Train-Serve Skew Prevention:** Ensure features are engineered, encoded, and formatted identically during both training and real-time prediction.
*   **Secure Microservices Architecture:** Containerize and isolate core operations (authentication, model serving, metadata tracking, and client-facing routing).
*   **Production-Ready UI:** Provide an intuitive clinical form with inputs validation and prediction history tracking.

---

## 🏗️ 2. Architectural Design

The platform uses a microservices architecture to segregate concerns and secure communication paths:

```text
       🌐 React UI Client (Port 3000)
                    │
                    ▼ HTTP Requests
     ┌─────────────────────────────────────────┐
     │        BFF Service (API Gateway)        │
     │         (FastAPI, Exposes Port 8000)    │
     └──────┬───────────────────────────┬──────┘
            │ Proxy                     │ Proxy
     ┌──────▼──────┐             ┌──────▼──────────────┐
     │ auth-service│             │ prediction-service  │
     │ (Port 8001) │             │ (Port 8003)         │
     └──────┬──────┘             └──────┬──────────┬───┘
            │                           │          │ Polls
            │                           │    ┌─────▼───────────────┐
            │                           │    │model-mgmt-service   │
            │                           │    │(Port 8004)          │
            │                           │    └─────┬───────────────┘
            │                           │          │ Reads/Writes
     ┌──────▼───────────────────────────▼──────────▼───────────────┐
     │                  Relational Database: postgres              │
     │             (cancer-db App DB: Exposes Port 55432)          │
     └─────────────────────────────────────────────────────────────┘
```

### Component Details
1.  **Frontend ([frontend/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/frontend)):** Developed in React and Material-UI. It handles patient authentication pages, the clinical input form, user profile details, and historical predictions visualization using interactive charts (`recharts`).
2.  **BFF Service ([services/bff-service/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/services/bff-service)):** A lightweight FastAPI proxy server. It is the only service exposing public ports. It manages CORS policies and routes incoming client requests to backend microservices over private networks.
3.  **Auth Service ([services/auth-service/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/services/auth-service)):** Manages user credentials (hashing passwords using bcrypt) and session validation (issuing and signing JWT tokens).
4.  **Prediction Service ([services/prediction-service/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/services/prediction-service)):** The ML inference engine. It loads the active Random Survival Forest model into memory, runs preprocessing, calculates probability curves, and logs transactions.
5.  **Model Management Service ([services/model-management-service/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/services/model-management-service)):** Tracks available model files and metadata (C-index, training metrics) in the database. Exposes REST endpoints to query and update the active "production" version.
6.  **Shared Library ([shared/shared-transformers/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/shared/shared-transformers)):** Contains constants, clinical enums, and the custom `SeerFeatureEngineer` transformer.
7.  **Databases:**
    *   **Main DB (`cancer-db`):** PostgreSQL storing relational schemas for users, profiles, logs, and model versions.
    *   **Cache (`cancer-cache`):** Redis caching serialized active pipelines.
    *   **Data Warehouse (`cancer-warehouse`):** PostgreSQL simulating the BigQuery analytics environment for ETL and training data storage.

---

## 🗄️ 3. Database Schema Definitions

### 1. App Relational Schema (`cancer-db`)

```sql
-- Users Table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'patient',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Prediction History Table
CREATE TABLE prediction_history (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    feature_vector JSONB,
    probability FLOAT,
    risk_level VARCHAR(20),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Model Versions Table
CREATE TABLE model_versions (
    version VARCHAR(50) PRIMARY KEY,
    storage_path VARCHAR(500) NOT NULL,
    status VARCHAR(20) DEFAULT 'staging' NOT NULL,
    metrics JSONB,
    training_date TIMESTAMP,
    training_samples INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    promoted_at TIMESTAMP,
    archived_at TIMESTAMP
);
```

---

## 🔄 4. Data Flow Processes

### A. Prediction Request Flow
1.  **UI Submit:** The doctor clicks "Get Prediction" sending raw form inputs to the BFF Gateway (`POST /api/predict`).
2.  **Gateway Routing:** The BFF validates request timeouts and proxies the request to the private `prediction-service`.
3.  **Authentication:** The `prediction-service` validates the JWT signature in the request headers or cookies.
4.  **Model Loading & Execution:**
    *   If the active model is a unified **scikit-learn Pipeline**, the raw dictionary is converted to a pandas DataFrame and fed into `model.predict_survival_function(df_input)`.
    *   If it is a legacy estimator, the raw inputs are preprocessed manually using `FeatureProcessor` and run through the Random Survival Forest estimator.
5.  **Risk Level Calculation:** Recurrence risk probability is calculated by interpolating survival probabilities at the requested timeframe (e.g. `query_years * 12` months).
6.  **Persistence & Return:** The prediction is logged in `prediction_history` database and the computed risk details, interpretation text, and survival curve are returned to the user.

### B. Automated Model Hot-Reloading Lifecycle
1.  **Background Thread:** The `prediction-service` starts a daemon thread (`ModelLoader`) that runs in the background.
2.  **Polling:** Every 6 hours, it calls the `model-management-service` endpoint `GET /api/v1/models/production`.
3.  **Reloading:** If the active production version in the database is different from the model currently loaded in memory, it pulls the new `.pkl` model file, swaps it in memory, and updates the local Redis cache.

---

## 📊 5. Data Engineering & ML Pipelines

### Raw Data Loading (`load_raw_seer.py`)
Loads raw SEER registry data from CSV in sequential chunks of 100k rows, performing basic null handling and type casts, and writes the raw records to the `raw_seer` table in `cancer-warehouse`.

### Analytics Engineering (dbt transformations)
The dbt project `seer_warehouse` executes a modular SQL-based DAG:
*   **Staging (`stg_seer_raw`):** Standardizes column headers and converts raw clinical tags into standard data types.
*   **Intermediate (`int_recurrence_target`):** Creates recurrence targets by grouping patients, checking if sequence indicators indicate recurrence (e.g., sequence >= 2 of same site cancer), and calculating gap months.
*   **Marts:**
    *   `fct_training_data_raw.sql` materializes a table of raw text fields that mirror the API structure, used to train unified pipeline estimators.
    *   `fct_training_data.sql` materializes preprocessed columns for legacy estimators.

### Machine Learning Pipeline
*   **Algorithm:** Random Survival Forest (RSF) from `scikit-survival`. RSF handles survival prediction on right-censored data (patients who haven't recurred by the time the study concludes).
*   **Train-Serve Skew Protection:** The ML Pipeline incorporates custom scikit-learn transformers (`SeerFeatureEngineer`) directly inside a unified `Pipeline` along with `ColumnTransformer` and `RandomSurvivalForest`.
    *   **Benefit:** Training and real-time serving run the exact same codebase, preventing discrepancies.

---

## 🛠️ 6. Local Setup, Audits & Verification

Please refer to [local_plan.md](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/local_plan.md) for detailed instructions on spinning up the local services, checking database schemas, running unit tests, and verifying local endpoints.
