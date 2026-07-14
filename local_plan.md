# Cancer Recurrence Platform — Local Development Status & Plan

This document tracks the steps, design choices, audits, and fixes applied during Phase 1: Local Development.

---

## Completed Steps

### 1. Infrastructure & Databases
*   Set up local directory structure.
*   Configured Docker Compose configuration for multi-service setup:
    *   **Main Database:** PostgreSQL `cancer-db` exposed on port `55432` for app transactional data.
    *   **In-Memory Cache:** Redis `cancer-cache` running internally on port `6379`.
    *   **Data Warehouse Simulation:** PostgreSQL `cancer-warehouse` (simulating BigQuery) exposed on port `5433`.
*   Implemented database migrations via SQL scripts:
    *   `01_init_db.sql` creates baseline tables (`users`, `user_profiles`, `prediction_history`, etc.).
    *   `02_model_versions_migration.sql` creates `model_versions` table with enum-based status (`staging`, `production`, `archived`, `failed`) and seeds the initial production version `rsf_seer_v1.0.0`.

### 2. Shared Libraries & Transformers
*   Structured [shared/shared-transformers/](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/shared/shared-transformers) package with setuptools.
*   Created constants defining clinical enums (e.g. `CancerSite`, `BiomarkerStatus`, etc.) matching SEER datasets.
*   Implemented unified `SeerFeatureEngineer` custom scikit-learn transformer to prevent Train-Serve skew.

### 3. Backend Microservices
*   **Auth Service:** Implemented asynchronous database sessions, JWT sign/verify, password hashing (bcrypt), registration, login, and `/me` routes.
*   **BFF Service:** Configured reverse proxies for `/api/auth` and `/api/predict` routes with centralized CORS and httpx timeout configurations.
*   **Prediction Service:** Configured custom inference engine, model polling thread (every 6 hours) to check for newer production models, and dynamic history tracking.
*   **Model Management Service:** Developed API endpoints to register, list, promote, rollback, and delete models from the model registry.

### 4. Frontend Client
*   Developed single-page React app using Material-UI and React Query.
*   Implemented dynamic form validation (e.g., locking breast cancer biomarkers when non-applicable).
*   Developed Prediction History page with status chips indicating risk levels.
*   Created Account Profile page showing patient registration metadata.

---

## Code Audit & Applied Fixes

During local development, we audited the full project and successfully fixed several bugs:

| Service | File | Issue | Fix Applied |
| :--- | :--- | :--- | :--- |
| **Prediction Service** | [main.py](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/services/prediction-service/app/main.py) | `NameError: name 'model_loader' is not defined` when hitting root `/` | Moved `model_loader` to module-level imports. |
| **Prediction Service** | [predictor.py](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/services/prediction-service/app/inference/predictor.py) | Train-Serve mismatch: manual feature processing crashed when loading new unified Pipeline models | Updated `predict_recurrence` to detect scikit-learn `Pipeline` objects and pass raw DataFrames. |
| **Shared Library** | [pipeline_transformers.py](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/shared/shared-transformers/transformers/pipeline_transformers.py) | `AttributeError` on missing optional columns during data transformations | Replaced `.get(col, default)` calls with a robust `_get_series` helper returning pandas Series. |
| **Frontend** | [History.tsx](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/frontend/src/pages/History.tsx) | Mapped risk colors default to gray for `Moderate` and `Very High` levels | Added explicit mappings in `getRiskColor` to support all four risk levels. |
| **Frontend** | [LoginForm.tsx](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/frontend/src/components/auth/LoginForm.tsx), [RegisterForm.tsx](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/frontend/src/components/auth/RegisterForm.tsx) | Auth links used native anchor `href` causing full browser page reloads | Converted links to React Router `RouterLink` components for seamless SPA routing. |
| **Frontend** | [Header.tsx](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/frontend/src/components/layout/Header.tsx), [App.tsx](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/frontend/src/App.tsx) | Dropdown menu "Profile" link was a dead route | Created the [Profile.tsx](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/frontend/src/pages/Profile.tsx) page and registered the route in the router. |

---

## Local Testing & Verification

1.  **Shared Transformer Unit Tests:**
    *   Created `test_pipeline_transformers.py` containing test cases for basic feature engineering and missing column fallbacks.
    *   Ran unit tests successfully using the local virtual environment:
        ```bash
        $env:PYTHONPATH="shared/shared-transformers"
        .\.venv\bin\python -m pytest shared/shared-transformers/tests/
        ```
        **Result:** `2 passed in 1.48s`

2.  **Local API Verification via BFF Gateway:**
    *   Sourced local images and built Python microservices without hitting registry rate limits:
        ```bash
        docker compose up --build --pull never
        ```
    *   Queried prediction and auth health check endpoints through BFF (`localhost:8000`), verifying all downstream microservices and Redis/PostgreSQL connections:
        ```bash
        # Prediction Service
        curl http://localhost:8000/api/predict/health
        # Response: {"status":"healthy","service":"prediction-service","model_version":"rsf_seer_v1.0.0","model_status":"loaded"}
        
        # Auth Service
        curl http://localhost:8000/api/auth/health
        # Response: {"status":"healthy","service":"auth-service"}
        ```

3.  **Frontend Live Dev Execution:**
    *   Started the React local development server:
        ```bash
        cd frontend
        npm start
        ```
        **Result:** Dev server compiling successfully and listening on [http://localhost:3000](http://localhost:3000).
