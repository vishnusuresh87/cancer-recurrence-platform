"""
Retrain RSF model using data from DBT-transformed fct_training_data table
"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sksurv.ensemble import RandomSurvivalForest
from sksurv.util import Surv
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
from pathlib import Path
from datetime import datetime
import json

print("=" * 80)
print("Retraining RSF Model from DBT-Transformed Data")
print("=" * 80)

# Connect to warehouse
engine = create_engine('postgresql://warehouse_user:warehouse_pass@localhost:5433/seer_warehouse')

# Load training data from DBT
print("Loading data from fct_training_data...")
df = pd.read_sql("SELECT * FROM fct_training_data", engine)
print(f"Loaded {len(df):,} rows")

# Feature columns (28 features)
FEATURE_COLUMNS = [
    'age_numeric', 'sex', 'cancer_site', 'harmonized_grade', 'harmonized_stage',
    'tumor_size_mm', 'histology_code', 'laterality', 'nodes_positive', 'node_ratio',
    'any_metastasis_at_dx', 'mets_bone', 'mets_liver', 'mets_lung', 'mets_brain',
    'lvi', 'surgery_performed', 'radiation_type', 'chemotherapy_binary', 'treatment_intensity',
    'surgery_radiation_sequence', 'days_to_treatment', 'er_status', 'pr_status', 'her2_status',
    'breast_receptor_subtype', 'marital_status', 'income_level',
]

# Encode categorical variables
# is_numeric_dtype handles int/float/bool correctly — only encode string/object columns
print("Encoding features...")
encoders = {}
df_encoded = df.copy()

for col in FEATURE_COLUMNS:
    if not pd.api.types.is_numeric_dtype(df_encoded[col]):
        le = LabelEncoder()
        df_encoded[col] = df_encoded[col].fillna('Unknown').astype(str)
        df_encoded[col] = le.fit_transform(df_encoded[col])
        encoders[col] = le
    else:
        # Numeric/bool columns: ensure NaN → -1, booleans become 0/1 naturally
        df_encoded[col] = pd.to_numeric(df_encoded[col], errors='coerce')

print(f"  Encoded {len(encoders)} categorical columns")

# Prepare X and y
X = df_encoded[FEATURE_COLUMNS].fillna(-1).values
y = Surv.from_arrays(
    event=df_encoded['recurred'].astype(bool).values,
    time=df_encoded['time_to_recurrence_months'].values
)

print(f"Feature matrix: {X.shape}")
print(f"Target: {len(y)} samples")

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training set: {len(X_train):,}")
print(f"Test set: {len(X_test):,}")

# Train RSF
print("Training Random Survival Forest...")
rsf = RandomSurvivalForest(
    n_estimators=300,
    min_samples_leaf=15,
    max_features='sqrt',
    n_jobs=-1,
    random_state=42,
    verbose=1
)

rsf.fit(X_train, y_train)

# Evaluate
train_score = rsf.score(X_train, y_train)
test_score = rsf.score(X_test, y_test)

print(f"\nC-index (train): {train_score:.4f}")
print(f"C-index (test):  {test_score:.4f}")

# Save model with new version
version = "rsf_seer_v2.0.0"
model_dir = Path("models")
model_dir.mkdir(exist_ok=True)

joblib.dump(rsf, model_dir / f"{version}.pkl")
joblib.dump(encoders, model_dir / f"{version}_encoders.pkl")
joblib.dump(FEATURE_COLUMNS, model_dir / f"{version}_feature_names.pkl")

metadata = {
    "model_version": version,
    "training_date": datetime.now().isoformat(),
    "training_samples": len(X_train),
    "test_samples": len(X_test),
    "c_index_train": float(train_score),
    "c_index_test": float(test_score),
    "data_source": "DBT fct_training_data",
}

with open(model_dir / f"{version}_metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\n✅ Model saved: {version}")
print(f"Register it with Model Management Service:")
print(f"  POST /api/v1/models/")



