# Cancer Recurrence Platform — Cloud Deployment Plan

This document outlines the deployment strategy for migrating the platform from a local Docker Compose setup to a production-grade cloud infrastructure on Google Cloud Platform (GCP) using Google Kubernetes Engine (GKE).

---

## Cloud Infrastructure Architecture

```text
                                  [ INTERNET ]
                                        │
                                        ▼ HTTPS (Port 443)
                            ┌───────────────────────┐
                            │  Cloud Load Balancer  │
                            └───────────┬───────────┘
                                        │
                                        ▼ Private Subnet
┌─────────────────────────────────────────────────────────────────────────────┐
│  Google Kubernetes Engine (GKE) Cluster                                      │
│                                                                             │
│               ┌──────────────────────────────────────────────┐              │
│               │             Kong Ingress Controller          │              │
│               └──────────────────────┬───────────────────────┘              │
│                                      │ (Proxy requests)                     │
│                 ┌────────────────────┴─────────────────────┐                │
│                 │               bff-service                │                │
│                 └───────┬──────────────────────────┬───────┘                │
│                         │ (Internal Route)         │ (Internal Route)       │
│               ┌─────────▼─────────┐      ┌─────────▼─────────┐              │
│               │    auth-service   │      │prediction-service │              │
│               └───────────────────┘      └─────────┬─────────┘              │
│                                                    │ Polling                │
│                                          ┌─────────▼─────────┐              │
│                                          │ model-management  │              │
│                                          └───────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
      │                              │                           │
      ▼ Private SQL Connection       ▼ Memorystore Protocol      ▼ IAM / GCS API
┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────┐
│     Cloud SQL (Postgres)  │  │   Cloud Memorystore Redis │  │ Cloud Storage │
│ (cancer_db transactional) │  │  (model / token caching)  │  │ (Model files) │
└───────────────────────────┘  └───────────────────────────┘  └───────────────┘
```

---

## GCP Resource Mapping

To ensure security, scalability, and high-availability, we map our local Docker services to dedicated GCP managed offerings:

| Local Component | GCP Production Component | Rationale |
| :--- | :--- | :--- |
| **`postgres`** | **Cloud SQL for PostgreSQL** | Managed backups, multi-zone replication, automated patches. |
| **`redis`** | **Cloud Memorystore for Redis** | High-availability, in-memory caching scale, zero-management. |
| **`bigquery-local`** | **Google BigQuery** | Highly scalable analytics data warehouse hosting 10M+ SEER records. |
| **Local models path** | **Google Cloud Storage (GCS)** | Secure, versioned object store (`gs://cancer-models/`) for model `.pkl` artifacts. |
| **Microservices** | **Google Kubernetes Engine (GKE)** | Autoscaling, self-healing, rolling updates, secure secrets management. |
| **BFF gateway** | **Kong Ingress Controller / Gateway** | Centralized API management, rate limiting, CORS policies, SSL termination. |

---

## Step-by-Step Deployment Strategy

### Phase 1: Infrastructure as Code (IaC) via Terraform
1.  **Network Setup:** Provision a Virtual Private Cloud (VPC) with public and private subnets, Cloud NAT (allowing private GKE nodes to contact the internet without public IPs), and Private Service Connect (for databases).
2.  **Databases:** 
    *   Create a **Cloud SQL (PostgreSQL 15)** instance with private IP only.
    *   Create a **Cloud Memorystore for Redis** instance in the private subnet.
3.  **Storage:** Create a version-controlled **Google Cloud Storage (GCS)** bucket (`gs://cancer-platform-models/`).
4.  **Compute:** Spin up a regional **GKE Standard** cluster (3 nodes across different zones for high-availability) with Workload Identity enabled.

### Phase 2: CI/CD Pipeline & Artifact Registry
1.  **Registry:** Setup **Google Artifact Registry** repositories to store Docker images securely.
2.  **Pipeline (Cloud Build / GitLab CI):** Create pipelines triggered by git commits:
    *   **CI:** Lint code, run pytest suites, check typescript compiler.
    *   **Build:** Build Docker images with tags matching the git commit SHA.
    *   **Push:** Push built images to Artifact Registry.
    *   **CD:** Update Kubernetes manifests or trigger ArgoCD to apply changes to GKE.

### Phase 3: Kubernetes Configurations (YAMLs)
1.  **ConfigMaps & Secrets:** Set up Kubernetes ConfigMaps for environment variables and use **External Secrets Operator** integrated with **Google Secret Manager** to securely load passwords and JWT keys into pods.
2.  **Deployments:**
    *   Deploy `auth-service`, `prediction-service`, `model-management-service`, and `bff-service` with `HorizontalPodAutoscaler` (scaling based on CPU/Memory load).
    *   Configure `readinessProbe` and `livenessProbe` on all microservices pointing to their `/health` endpoints.
3.  **Services:** Expose services internally using ClusterIP.
4.  **Ingress:** Deploy **Kong Ingress Controller** exposed via a External Cloud Load Balancer with SSL certificates managed by Google Managed Certificates.

### Phase 4: Data Pipeline & Model Deployment
1.  **Data Warehouse:** Create BigQuery datasets and grant write permissions to the DBT runner service account.
2.  **DBT Run:** Run DBT pipelines in GCP (e.g. running on Cloud Run or Composer) to build the `fct_training_data` table.
3.  **Model Register:** Run training jobs on Vertex AI, outputting the pipeline model to the GCS bucket, and register it via `model-management-service` REST endpoints.
4.  **Traffic Routing:** Enable model hot-reloading. The GKE prediction-service pods will poll the model-management-service and hot-reload the `.pkl` files directly from GCS.

---

## Monitoring & Reliability

1.  **Metrics:** Install **Prometheus Operator** in GKE. Expose custom endpoints `/metrics` on microservices (using `prometheus_client` in FastAPI) to track latency, request counts, and prediction outcomes.
2.  **Dashboard:** Deploy **Grafana** connected to Prometheus to visualize cluster health and business performance.
3.  **Logging:** Route all stdout/stderr from GKE containers directly to **Cloud Logging (Stackdriver)** for centralized analysis and debugging.
