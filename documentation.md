# Cancer Recurrence Platform — Comprehensive Project Documentation

This report serves as the complete technical manual for the Cancer Recurrence Prediction Platform. It details the system architecture, API endpoints, core business logic, machine learning pipelines, dbt modeling DAG, and local development auditing.

---

## 1. Project Overview & Objectives

The platform provides evidence-based survival predictions estimating the probability of cancer recurrence over a variable time horizon (e.g. 5-year or 10-year risk). It is trained on the SEER (Surveillance, Epidemiology, and End Results) database which tracks clinical characteristics, treatments, and vital statistics for millions of historical cancer cases.

---

## 2. System Architecture & Microservice Breakdown

The platform follows a modular microservices architecture designed to decouple the frontend client from back-end database access and ML workloads. Internal microservices communicate securely inside a private network, and the Backend-For-Frontend (BFF) acts as the single gateway.

### BFF Service (Backend-For-Frontend)
*   **Role:** Exposes port 8000. It is the sole gateway intercepting public HTTP requests from the React client.
*   **Routing Logic:** Proxies incoming requests to private backend ports using `httpx.AsyncClient` connections:
    *   Requests to `/api/auth/*` are routed to the `auth-service` (port 8001).
    *   Requests to `/api/predict/*` are routed to the `prediction-service` (port 8003).
*   **Security:** Manages Cross-Origin Resource Sharing (CORS) configurations, stripping headers like `Host` to hide downstream details, and terminates proxy request timeouts (30.0s for predictions to accommodate ML workloads, 10.0s for others).

### Auth Service
*   **Role:** Handles user administration and authorization inside the private network (port 8001).
*   **Identity Logic:** Registers users, hashes passwords using the `passlib` bcrypt algorithm, verifies credentials, and issues JSON Web Tokens (JWT) signed using a server-side secret key (`HS256`).
*   **Token Verification:** Injects HTTP-only cookie parameters (`access_token`) on registration or login, enabling the BFF and frontend to authenticate requests without caching tokens in public JS memory.

### Prediction Service
*   **Role:** Serves as the core inference engine (port 8003).
*   **Data Processing:** Preprocesses raw JSON payloads into numeric arrays using shared transformers, queries predictions from the in-memory survival model, and saves prediction logs.
*   **Coordination:** Initiates a daemon thread at startup to poll the `model-management-service` for active model files.

### Model Management Service
*   **Role:** Acts as the ML model registry (port 8004).
*   **Registry Logic:** Tracks model metadata (c-index, sample size, date) and file storage paths. When a model version is updated or marked as `production`, it notifies polling prediction servers.

---

## 3. Database Schema Specifications

The PostgreSQL application database (`cancer-db`) is structured to support transactional states across multiple microservices.

### Table: `users`
Tracks patient and clinician accounts.
*   `user_id`: UUID (Primary Key), defaults to `gen_random_uuid()`
*   `email`: VARCHAR(255) (Unique, Indexed, Nullable=False)
*   `password_hash`: VARCHAR(255) (Nullable=False)
*   `role`: VARCHAR(20) (Defaults to 'patient')
*   `created_at`: TIMESTAMP (Defaults to `NOW()`)
*   `last_login`: TIMESTAMP (Nullable=True)

### Table: `prediction_history`
Maintains logs of all generated prediction outputs.
*   `prediction_id`: UUID (Primary Key), defaults to `gen_random_uuid()`
*   `user_id`: UUID (ForeignKey -> `users.user_id`, Indexed)
*   `feature_vector`: JSONB (Stores raw inputs payload)
*   `probability`: FLOAT (Recurrence percentage)
*   `risk_level`: VARCHAR(20) (Low, Moderate, High, Very High)
*   `model_version`: VARCHAR(50) (Active model tag)
*   `created_at`: TIMESTAMP (Defaults to `NOW()`, Indexed)

### Table: `model_versions`
Coordinates model lifecycle tracking.
*   `version`: VARCHAR(50) (Primary Key, e.g. `rsf_seer_v1.0.0`)
*   `storage_path`: VARCHAR(500) (Local disk file path or GCS bucket URL)
*   `status`: model_status (Enum: staging, production, archived, failed)
*   `metrics`: JSONB (Model evaluation indices)
*   `training_date`: TIMESTAMP
*   `training_samples`: INTEGER
*   `created_at`: TIMESTAMP (Defaults to `NOW()`)
*   `promoted_at`: TIMESTAMP
*   `archived_at`: TIMESTAMP

---

## 4. Preprocessing Logic & Shared Transformers

The `SeerFeatureEngineer` class located in [shared/shared-transformers/transformers/pipeline_transformers.py](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/shared/shared-transformers/transformers/pipeline_transformers.py) ensures that clinical features are engineered and mapped identically during training and inference.

### Safe Column Retrieval (`_get_series`)
To prevent crashes when input payloads lack optional columns, a helper method `_get_series` is implemented:
```python
def _get_series(self, df, col, default_val):
    if col in df.columns:
        return df[col]
    return pd.Series(default_val, index=df.index)
```
This guarantees that missing optional keys return a Series initialized with appropriate default fallbacks (e.g. `Unknown` or `-1`) matching the dataframe index, enabling operations like `.map()` and `.fillna()` to execute safely.

### Feature Mapping Logic
*   **Age Groups:** Map nominal ranges to representative numeric midpoints:
    *   `20-24 years` -> `22.0`
    *   `50-54 years` -> `52.0`
    *   `85+ years` -> `87.0`
*   **Tumor Grade:** Map grading levels to numeric integers:
    *   `Grade I` / `Well differentiated` -> `1`
    *   `Grade II` / `Moderately differentiated` -> `2`
    *   `Grade III` / `Poorly differentiated` -> `3`
    *   `Grade IV` / `Undifferentiated` -> `4`
    *   Fallbacks -> `-1`
*   **Harmonized Stage:** Maps SEER stage summaries:
    *   `In situ` -> `0`
    *   `Localized` -> `1`
    *   `Regional` -> `2`
    *   `Distant` -> `3`
*   **Days to Treatment:** Bucketed durations are mapped to average midpoints:
    *   `0-30 days` -> `15`
    *   `31-90 days` -> `60`
    *   `91+ days` -> `120`
*   **Histology Broad:** Maps broad clinical labels to specific ICD-O-3 integer codes used in training:
    *   `Adenocarcinoma` -> `8140.0`
    *   `Squamous cell carcinoma` -> `8070.0`
    *   `Ductal carcinoma` -> `8500.0`
    *   `Lobular carcinoma` -> `8520.0`
    *   `Small cell carcinoma` -> `8041.0`
    *   `Large cell carcinoma` -> `8012.0`
    *   `Other` / `Unknown` -> `8000.0`
*   **Lymph Node Ratio:** Computed as `node_ratio = nodes_positive / nodes_examined`. If `nodes_examined <= 0`, it defaults to `-1.0` (indicating node status unknown).
*   **Treatment Intensity:** A composite score calculated by summing treatment binary flags:
    `treatment_intensity = surgery_performed + chemotherapy_binary + radiation_binary` (Range: 0 to 3).
*   **Receptor Subtype Matrix:** For breast cancer sites, maps estrogen receptor (ER), progesterone receptor (PR), and HER2 status:
    *   ER positive or PR positive, and HER2 positive -> `HR+/HER2+`
    *   ER positive or PR positive, and HER2 negative -> `HR+/HER2-`
    *   ER negative and PR negative, and HER2 positive -> `HR-/HER2+`
    *   ER negative, PR negative, and HER2 negative -> `Triple Negative`

---

## 5. In-Memory Hot-Reloading Mechanism

The `ModelLoader` class in [services/prediction-service/app/inference/model_loader.py](file:///D:/GitHub/Data%20Mining/cancer-recurrence-platform/services/prediction-service/app/inference/model_loader.py) maintains the loaded model lifecycle.

### Background Poller Daemon
1.  **Thread Initialization:** At startup, `ModelLoader` spins up a background daemon thread running an infinite loop:
    ```python
    def _poll_loop(self):
        while not self.shutdown_event.is_set():
            try:
                self.sync_with_production()
            except Exception as e:
                print(f"Model sync failed: {e}")
            self.shutdown_event.wait(self.poll_interval)
    ```
2.  **State Verification:** It sends a request to the model registry endpoint `GET /api/v1/models/production`.
3.  **Hot Swap:** If the registry returns a model version string that differs from `self.model_version`, it downloads the new `.pkl` binary path, invokes `joblib.load()` to deserialize the new estimator pipeline, and assigns it to `self.model`.
4.  **Redis Caching:** Once loaded, it serializes the active model using `joblib.dumps()` and caches it in Redis with a 24-hour TTL. Distributed API instances can pull this cached binary directly from memory, reducing container startup overhead.

---

## 6. Training & Retraining Pipelines

### Baseline Training Pipeline (`seer_training_pipeline.py`)
This script executes a multi-step workflow on raw data:
1.  **Sequential Chunking:** Reads raw SEER database exports (`seer_data_export.csv`) in sequential chunks of 100k rows. This preserves family/patient record ordering since clinical histories for the same patient appear contiguously.
2.  **Random Sampling:** Extract a representative sample of 200k rows for model training.
3.  **Target Creation & Censoring:** Recurrence events are computed by checking if a patient has multiple records. If a patient has multiple primary tumors:
    *   If sequence indicator >= 2, the site is identical, and the duration gap between diagnoses >= 3 months, it is flagged as a recurrence (`recurred = 1`), and the target survival duration is set to the gap interval.
    *   If no second record exists, the patient is flagged as right-censored (`recurred = 0`), meaning they did not recur within the observed timeframe, and the target survival duration is mapped to their survival months.
4.  **Estimator Fitting:** Encodes target arrays into survival formats using `sksurv.util.Surv.from_arrays(event, time)`. It fits a `RandomSurvivalForest` using `scikit-survival`, calculating tree node splits using log-rank test statistics.

### Skew-Free Pipeline Retraining (`retrain_from_dbt.py`)
To prevent discrepancies between offline training and online serving, the retraining script creates a unified scikit-learn `Pipeline`:
1.  **Data Extraction:** Queries raw training sets (`fct_training_data_raw`) directly from the analytics database.
2.  **Pipeline Construction:**
    ```python
    pipeline = Pipeline([
        ('feature_engineer', SeerFeatureEngineer()),
        ('preprocessor', ColumnTransformer(transformers=[
            ('cat', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), categorical_cols),
            ('num', SimpleImputer(strategy='constant', fill_value=-1.0), numeric_cols)
        ])),
        ('rsf', RandomSurvivalForest(n_estimators=300, min_samples_leaf=15, n_jobs=-1, random_state=42))
    ])
    ```
3.  **Unified Fit:** Invoking `pipeline.fit(X_train, y_train)` fits all preprocessing and estimator weights simultaneously.
4.  **Evaluation:** Evaluates the model using the Harrell's Concordance Index (C-index) on the test split to assess survival risk ordering.
5.  **Artifact Generation:** Serializes the complete `Pipeline` object into a single `.pkl` file.

---

## 7. Data Analytics Engineering with dbt

The dbt project `seer_warehouse` performs structured transformations within the simulated data warehouse.

```text
raw_seer (Table) ──> stg_seer_raw (View) ──> int_recurrence_target (View) ──> fct_training_data_raw (Table)
```

### 1. Staging (`stg_seer_raw.sql`)
Maps raw source CSV headers to clean, standardized fields:
*   Renames raw fields like `"Regional nodes positive (1988+)"` to `nodes_positive`.
*   Casts raw columns to numeric data types.

### 2. Intermediate (`int_recurrence_target.sql`)
Computes survival time horizons and target events:
*   Groups records by `patient_id` and orders them chronologically.
*   Applies window functions to compare sequence numbers and diagnostic gaps between first and second primary tumors.
*   Derives the boolean target `recurred` and duration target `time_to_recurrence_months`.

### 3. Marts (`fct_training_data_raw.sql`)
Assembles features for training:
*   Extracts raw clinical labels (e.g. `mets_bone`, `lvi`, etc.) and filters records to ensure survival times are within valid ranges (0 to 20 years).
*   This table is loaded directly by `retrain_from_dbt.py` to train unified pipelines.

---

## 8. Audit Findings & verified Local Status

During local development, we completed a project audit and resolved several bugs:
*   **Prediction Service NameError:** Resolved a startup crash in `main.py` by moving `model_loader` to module-level imports.
*   **Pipeline Mismatch:** Rewrote `predictor.py` to support both raw estimators and unified `Pipeline` objects.
*   **Missing Columns Crash:** Implemented the `_get_series` helper in `pipeline_transformers.py` to handle missing inputs.
*   **Routing & Page Improvements:** Replaced auth anchor tags with `RouterLink` to enable client-side SPA routing, updated risk levels mapping colors on the history page, and added a user Profile page.

All local fixes have been verified by executing the unit test suite and checking local endpoints via the BFF gateway. The entire local dev stack is running and clean.
