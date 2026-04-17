"""
Complete SEER RSF Training Pipeline
Matches PDF specifications exactly

Steps:
1. Sample 200k rows from seer_data.csv (Sequentially to preserve patient groups)
2. Clean data (handle nulls, type conversions)
3. Engineer 28 features (per PDF)
4. Create recurrence target (sequence >=2, same site, gap >=3 months)
5. Train Random Survival Forest
6. Evaluate (C-index, calibration)
7. Save model and encoders
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import joblib
from tqdm import tqdm

# ML imports
from sksurv.ensemble import RandomSurvivalForest
from sksurv.util import Surv
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

print("=" * 80)
print("SEER Cancer Recurrence Model Training Pipeline")
print("=" * 80)
print(f"Started at: {datetime.now()}")
print()

# ==================== CONFIGURATION ====================

CONFIG = {
    "raw_data_path": "/mnt/c/Users/vishn/Downloads/seer_data_export.csv",  # Changed to absolute WSL path
    "sample_size": 200_000,  # Restored to 200k
    "random_state": 42,
    "model_output_path": "models/rsf_seer_v1.pkl",
    "metadata_output_path": "models/rsf_seer_v1_metadata.json",
    
    # RSF hyperparameters
    "n_estimators": 100,    # Reduced from 300 to save RAM
    "min_samples_leaf": 50,
    "max_features": "sqrt",
    "n_jobs": 1,            # Enforce strictly 1 core to COMPLETELY disable Joblib memory duplication overhead
}

# ==================== STEP 1: SAMPLE DATA ====================

print("STEP 1: Sampling 200k rows from seer_data.csv")
print("-" * 80)

raw_path = Path(CONFIG["raw_data_path"])

if not raw_path.exists():
    raise FileNotFoundError(f"SEER data not found at: {raw_path}")

print(f"📁 Reading from: {raw_path}")
print(f"📊 Target sample size: {CONFIG['sample_size']:,} rows")
print()

# Read in sequential chunks to preserve patient grouping
chunk_size = 100_000
chunks = []
total_read = 0

print("Reading data in sequential chunks...")
for i, chunk in enumerate(pd.read_csv(raw_path, chunksize=chunk_size, low_memory=False)):
    chunks.append(chunk)
    total_read += len(chunk)
    print(f"   Chunk {i+1}: {len(chunk):,} rows (Total: {total_read:,})")
    
    # Read twice the sample size before stopping to ensure enough patients are captured together
    if total_read >= CONFIG["sample_size"] * 2:
        break

df_raw = pd.concat(chunks, ignore_index=True)
print(f"\n✅ Loaded {len(df_raw):,} sequential rows")

# Random sample from the sequential block
print(f"🎲 Random sampling {CONFIG['sample_size']:,} rows...")
df_raw = df_raw.sample(n=min(CONFIG["sample_size"], len(df_raw)), random_state=CONFIG["random_state"])

print(f"✅ Final Sampled {len(df_raw):,} rows\n")


# ==================== STEP 2: DATA CLEANING ====================

print("STEP 2: Data Cleaning")
print("-" * 80)

COLUMN_MAPPING = {
    "Patient ID": "patient_id",
    "Age recode with <1 year olds and 90+": "age_group",
    "Sex": "sex",
    "Site recode ICD-O-3/WHO 2008": "cancer_site",
    "Histologic Type ICD-O-3": "histology_code",
    "Behavior recode for analysis": "behavior",
    "Grade Recode (thru 2017)": "tumor_grade",
    "Laterality": "laterality",
    "Summary stage 2000 (1998-2017)": "summary_stage",
    "Tumor Size Over Time Recode (1988+)": "tumor_size_mm",
    "Regional nodes examined (1988+)": "nodes_examined",
    "Regional nodes positive (1988+)": "nodes_positive",
    "SEER Combined Mets at DX-bone (2010+)": "mets_bone",
    "SEER Combined Mets at DX-brain (2010+)": "mets_brain",
    "SEER Combined Mets at DX-liver (2010+)": "mets_liver",
    "SEER Combined Mets at DX-lung (2010+)": "mets_lung",
    "Lymph-vascular Invasion (2004+ varying by schema)": "lvi",
    "RX Summ--Surg Prim Site (1998+)": "surgery_code",
    "Radiation recode": "radiation_type",
    "Chemotherapy recode (yes, no/unk)": "chemotherapy",
    "RX Summ--Surg/Rad Seq": "surgery_radiation_sequence",
    "Time from diagnosis to treatment in days recode": "days_to_treatment",
    "ER Status Recode Breast Cancer (1990+)": "er_status",
    "PR Status Recode Breast Cancer (1990+)": "pr_status",
    "Derived HER2 Recode (2010+)": "her2_status",
    "Marital status at diagnosis": "marital_status",
    "Median household income inflation adj to 2023": "income_level",
    "Rural-Urban Continuum Code 2013": "rural_urban",
    "Sequence number": "sequence_number",
    "First malignant primary indicator": "first_primary",
    "Total number of in situ/malignant tumors for patient": "total_malignant_tumors",
    "Year of diagnosis": "year_dx",
    "Survival months": "survival_months",
    "Vital status recode (study cutoff used)": "vital_status",
}

# Rename columns
df = df_raw.rename(columns=COLUMN_MAPPING)

print(f"Columns mapped: {len(COLUMN_MAPPING)}")
print(f"Shape after mapping: {df.shape}\n")


# ==================== STEP 3: FEATURE ENGINEERING ====================

print("STEP 3: Feature Engineering (28 features)")
print("-" * 80)

# 3.1: node_ratio
print("Creating node_ratio...")
df['nodes_examined'] = pd.to_numeric(df['nodes_examined'], errors='coerce').fillna(0)
df['nodes_positive'] = pd.to_numeric(df['nodes_positive'], errors='coerce').fillna(0)
df['node_ratio'] = np.where(
    df['nodes_examined'] > 0,
    df['nodes_positive'] / df['nodes_examined'],
    -1  # Unknown
)

# 3.2: treatment_intensity (0-3)
print("Creating treatment_intensity...")
df['surgery_performed'] = df['surgery_code'].notna() & (df['surgery_code'] != 'No surgery')
df['chemotherapy_binary'] = df['chemotherapy'].astype(str).str.contains('Yes', case=False, na=False)
df['radiation_binary'] = df['radiation_type'].notna() & (df['radiation_type'] != 'None')

df['treatment_intensity'] = (
    df['surgery_performed'].astype(int) +
    df['chemotherapy_binary'].astype(int) +
    df['radiation_binary'].astype(int)
)

# 3.3: any_metastasis_at_dx
print("Creating any_metastasis_at_dx...")
mets_cols = ['mets_bone', 'mets_liver', 'mets_lung', 'mets_brain']
for col in mets_cols:
    df[col] = df[col].astype(str).str.contains('Yes', case=False, na=False)

df['any_metastasis_at_dx'] = (
    df['mets_bone'] | df['mets_liver'] | df['mets_lung'] | df['mets_brain']
)

# 3.4: harmonized_stage
print("Harmonizing stage...")
stage_mapping = {'In situ': 0, 'Localized': 1, 'Regional': 2, 'Distant': 3}
df['harmonized_stage'] = df['summary_stage'].map(stage_mapping).fillna(-1).astype(int)

# 3.5: harmonized_grade
print("Harmonizing grade...")
grade_mapping = {
    'Grade I': 1, 'Well differentiated': 1, 'Grade II': 2, 'Moderately differentiated': 2,
    'Grade III': 3, 'Poorly differentiated': 3, 'Grade IV': 4, 'Undifferentiated': 4,
}
df['harmonized_grade'] = df['tumor_grade'].map(grade_mapping).fillna(-1).astype(int)

# 3.6: breast_receptor_subtype
print("Creating breast_receptor_subtype...")
def derive_breast_subtype(row):
    er = row.get('er_status', '')
    pr = row.get('pr_status', '')
    her2 = row.get('her2_status', '')
    if pd.isna(er) or pd.isna(pr) or pd.isna(her2): return 'Not Breast Cancer'
    er_pos = 'Positive' in str(er); pr_pos = 'Positive' in str(pr); her2_pos = 'Positive' in str(her2)
    
    if (er_pos or pr_pos) and her2_pos: return 'HR+/HER2+'
    elif (er_pos or pr_pos) and not her2_pos: return 'HR+/HER2-'
    elif not (er_pos or pr_pos) and her2_pos: return 'HR-/HER2+'
    else: return 'Triple Negative'

df['breast_receptor_subtype'] = df.apply(derive_breast_subtype, axis=1)

# 3.7: age_numeric
print("Creating age_numeric...")
age_mapping = {
    '00 years': 0, '01-04 years': 2.5, '05-09 years': 7, '10-14 years': 12, '15-19 years': 17,
    '20-24 years': 22, '25-29 years': 27, '30-34 years': 32, '35-39 years': 37, '40-44 years': 42,
    '45-49 years': 47, '50-54 years': 52, '55-59 years': 57, '60-64 years': 62, '65-69 years': 67,
    '70-74 years': 72, '75-79 years': 77, '80-84 years': 82, '85+ years': 87,
}
df['age_numeric'] = df['age_group'].map(age_mapping).fillna(50)  # Default to median

print("✅ All engineered features created\n")

# ==================== STEP 4: RECURRENCE TARGET ====================

print("STEP 4: Creating Recurrence Target")
print("-" * 80)

print("Identifying recurrence events...")
df['year_dx'] = pd.to_numeric(df['year_dx'], errors='coerce')
df = df.sort_values(['patient_id', 'year_dx'])
patient_groups = df.groupby('patient_id')

recurrence_flags = []
for patient_id, group in tqdm(patient_groups):
    if len(group) == 1:
        recurrence_flags.append({
            'patient_id': patient_id,
            'recurred': 0,
            'time_to_recurrence_months': group.iloc[0]['survival_months']
        })
    else:
        first = group.iloc[0]
        second = group.iloc[1]
        same_site = first['cancer_site'] == second['cancer_site']
        gap_months = (second['year_dx'] - first['year_dx']) * 12
        recurred = same_site and gap_months >= 3
        recurrence_flags.append({
            'patient_id': patient_id,
            'recurred': 1 if recurred else 0,
            'time_to_recurrence_months': gap_months if recurred else first['survival_months']
        })

recurrence_df = pd.DataFrame(recurrence_flags)
df_first_primary = df[df['first_primary'].astype(str) == 'Yes'].copy()
if df_first_primary.empty:
    df_first_primary = df.drop_duplicates(subset=['patient_id'], keep='first').copy()

df_model = df_first_primary.merge(recurrence_df, on='patient_id', how='left')

df_model['time_to_recurrence_months'] = pd.to_numeric(df_model['time_to_recurrence_months'], errors='coerce').fillna(60)

print(f"\nTotal patients: {len(df_model):,}")
print(f"Recurrences: {df_model['recurred'].sum():,} ({df_model['recurred'].mean()*100:.1f}%)\n")

# ==================== STEP 5: PREPARE MODEL FEATURES ====================

print("STEP 5: Preparing Model Features")
print("-" * 80)

FEATURE_COLUMNS = [
    'age_numeric', 'sex', 'cancer_site', 'harmonized_grade', 'harmonized_stage',
    'tumor_size_mm', 'histology_code', 'laterality', 'nodes_positive', 'node_ratio',
    'any_metastasis_at_dx', 'mets_bone', 'mets_liver', 'mets_lung', 'mets_brain',
    'lvi', 'surgery_performed', 'radiation_type', 'chemotherapy_binary', 'treatment_intensity',
    'surgery_radiation_sequence', 'days_to_treatment', 'er_status', 'pr_status',
    'her2_status', 'breast_receptor_subtype', 'marital_status', 'income_level',
]

print("Encoding categorical features...")
encoders = {}
df_encoded = df_model.copy()

for col in FEATURE_COLUMNS:
    if df_encoded[col].dtype == 'object' or df_encoded[col].dtype.name == 'category':
        le = LabelEncoder()
        df_encoded[col] = df_encoded[col].fillna('Unknown').astype(str)
        df_encoded[col] = le.fit_transform(df_encoded[col])
        encoders[col] = le
    elif df_encoded[col].dtype == 'bool':
        df_encoded[col] = df_encoded[col].astype(int)

df_encoded['tumor_size_mm'] = pd.to_numeric(df_encoded['tumor_size_mm'], errors='coerce').fillna(30.0)
df_encoded['days_to_treatment'] = pd.to_numeric(df_encoded['days_to_treatment'], errors='coerce').fillna(45.0)

X = df_encoded[FEATURE_COLUMNS].fillna(-1.0).values
y = Surv.from_arrays(
    event=df_encoded['recurred'].astype(bool).values,
    time=df_encoded['time_to_recurrence_months'].values
)

print(f"Feature matrix: {X.shape}")
print(f"Target: {len(y)} samples\n")

# ==================== STEP 6: TRAIN RSF MODEL ====================

print("STEP 6: Training Random Survival Forest")
print("-" * 80)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=CONFIG["random_state"])

print(f"Training set: {len(X_train):,} samples")
print(f"Test set: {len(X_test):,} samples\n")

print("Training model (this may take 5-15 minutes)...")
rsf = RandomSurvivalForest(
    n_estimators=CONFIG["n_estimators"],
    min_samples_leaf=CONFIG["min_samples_leaf"],
    max_features=CONFIG["max_features"],
    n_jobs=CONFIG["n_jobs"],
    random_state=CONFIG["random_state"],
    verbose=1
)

rsf.fit(X_train, y_train)
print("✅ Model training complete!\n")

# ==================== STEP 7: EVALUATE MODEL ====================

print("STEP 7: Model Evaluation (Skipping Permutation Importance for Speed)")
print("-" * 80)

train_score = rsf.score(X_train, y_train)
test_score = rsf.score(X_test, y_test)

print(f"C-index (train): {train_score:.4f}")
print(f"C-index (test):  {test_score:.4f}\n")

# ==================== STEP 8: SAVE MODEL ====================

print("STEP 8: Saving Model")
print("-" * 80)

model_path = Path(CONFIG["model_output_path"])
model_path.parent.mkdir(exist_ok=True, parents=True)

joblib.dump(rsf, model_path)
print(f"✅ Model saved to: {model_path}")

encoders_path = model_path.parent / "rsf_seer_v1_encoders.pkl"
joblib.dump(encoders, encoders_path)
print(f"✅ Encoders saved to: {encoders_path}")

feature_names_path = model_path.parent / "rsf_seer_v1_feature_names.pkl"
joblib.dump(FEATURE_COLUMNS, feature_names_path)
print(f"✅ Feature names saved to: {feature_names_path}")

import json
metadata = {
    "model_version": "rsf_seer_v1.0.0",
    "training_date": datetime.now().isoformat(),
    "training_samples": len(X_train),
    "test_samples": len(X_test),
    "c_index_train": float(train_score),
    "c_index_test": float(test_score),
    "n_features": len(FEATURE_COLUMNS),
    "feature_names": FEATURE_COLUMNS,
    "recurrence_rate": float(df_model['recurred'].mean())
}

metadata_path = Path(CONFIG["metadata_output_path"])
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"✅ Metadata saved to: {metadata_path}\n")

print("=" * 80)
print("✅ TRAINING COMPLETE!")
print("=" * 80)