"""
Retrain RSF model using Scikit-Learn Pipeline to eliminate Train-Serve skew
"""
import sys
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sksurv.ensemble import RandomSurvivalForest
from sksurv.util import Surv
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.impute import SimpleImputer
import joblib
from pathlib import Path
from datetime import datetime
import json

# Add shared transformers to path
sys.path.append(str(Path(__file__).parent.parent.parent / "shared"))
from shared_transformers.transformers.pipeline_transformers import SeerFeatureEngineer

print("=" * 80)
print("Retraining RSF Model with Pipeline (Train-Serve Skew Free)")
print("=" * 80)

# Connect to warehouse
engine = create_engine('postgresql://warehouse_user:warehouse_pass@localhost:5433/seer_warehouse')

# Load RAW training data from DBT
print("Loading data from fct_training_data_raw...")
df = pd.read_sql("SELECT * FROM fct_training_data_raw", engine)
print(f"Loaded {len(df):,} rows")

# Prepare X and y
X = df.drop(columns=['recurred', 'time_to_recurrence_months', 'patient_id'])
y = Surv.from_arrays(
    event=df['recurred'].astype(bool).values,
    time=df['time_to_recurrence_months'].values
)

print(f"Feature matrix: {X.shape}")
print(f"Target: {len(y)} samples")

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training set: {len(X_train):,}")
print(f"Test set: {len(X_test):,}")

# Build Pipeline Steps
print("Building Pipeline...")
feature_engineer = SeerFeatureEngineer()

categorical_cols = [
    'sex', 'cancer_site', 'histology_code', 'laterality', 'lvi', 'radiation_type', 
    'surgery_radiation_sequence', 'days_to_treatment', 'er_status', 'pr_status', 
    'her2_status', 'breast_receptor_subtype', 'marital_status', 'income_level'
]

numeric_cols = [
    'age_numeric', 'harmonized_grade', 'harmonized_stage', 'tumor_size_mm',
    'nodes_positive', 'node_ratio', 'any_metastasis_at_dx', 'mets_bone',
    'mets_liver', 'mets_lung', 'mets_brain', 'surgery_performed',
    'chemotherapy_binary', 'treatment_intensity'
]

# Note: encoded_missing_value=-1 handles NaNs seen during transform 
# but isn't strictly needed if we fillna before passing to OrdinalEncoder, 
# but we just use use_encoded_value for unknown categories.
try:
    cat_encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1, encoded_missing_value=-1)
except TypeError:
    # Older versions of sklearn don't have encoded_missing_value
    cat_encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)

preprocessor = ColumnTransformer(
    transformers=[
        ('cat', cat_encoder, categorical_cols),
        ('num', SimpleImputer(strategy='constant', fill_value=-1.0), numeric_cols)
    ],
    remainder='drop'
)

rsf = RandomSurvivalForest(
    n_estimators=300,
    min_samples_leaf=15,
    max_features='sqrt',
    n_jobs=-1,  # use all cores
    random_state=42,
    verbose=1
)

pipeline = Pipeline([
    ('feature_engineer', feature_engineer),
    ('preprocessor', preprocessor),
    ('rsf', rsf)
])

# Train RSF Pipeline
print("Training Random Survival Forest Pipeline...")
pipeline.fit(X_train, y_train)

# Evaluate
print("Evaluating model...")
train_score = pipeline.score(X_train, y_train)
test_score = pipeline.score(X_test, y_test)

print(f"\nC-index (train): {train_score:.4f}")
print(f"C-index (test):  {test_score:.4f}")

# Save the unified pipeline
version = "rsf_pipeline_v3.0.0"
model_dir = Path("models")
model_dir.mkdir(exist_ok=True)

joblib.dump(pipeline, model_dir / f"{version}.pkl")

metadata = {
    "model_version": version,
    "training_date": datetime.now().isoformat(),
    "training_samples": len(X_train),
    "test_samples": len(X_test),
    "c_index_train": float(train_score),
    "c_index_test": float(test_score),
    "data_source": "DBT fct_training_data_raw (Pipeline integrated)",
}

with open(model_dir / f"{version}_metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\n✅ Pipeline saved: {version}")
print(f"Register it with Model Management Service:")
print(f"  POST /api/v1/models/ with filepath: {version}.pkl")
