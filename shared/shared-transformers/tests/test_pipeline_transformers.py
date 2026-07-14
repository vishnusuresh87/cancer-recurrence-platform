import pytest
import pandas as pd
import numpy as np
from transformers.pipeline_transformers import SeerFeatureEngineer

def test_seer_feature_engineer_basic():
    engineer = SeerFeatureEngineer()
    
    # Test with standard input dict
    raw_patient = {
        "cancer_site": "Breast",
        "age_group": "50-54 years",
        "sex": "Female",
        "tumor_grade": "Grade III",
        "harmonized_stage": "Regional",
        "tumor_size_mm": 45,
        "histology_broad": "Ductal carcinoma",
        "laterality": "Left",
        "nodes_positive": 3,
        "nodes_examined": 10,
        "mets_bone": True,
        "mets_liver": False,
        "mets_lung": False,
        "mets_brain": False,
        "lvi": "Present",
        "surgery_performed": True,
        "radiation_type": "External Beam",
        "chemotherapy": True,
        "surgery_radiation_sequence": "Surgery before radiation",
        "days_to_treatment": "0-30 days",
        "er_status": "Positive",
        "pr_status": "Positive",
        "her2_status": "Negative",
        "marital_status": "Married",
        "income_level": "Medium",
    }
    
    df_out = engineer.transform(raw_patient)
    
    # Output should be a DataFrame with 28 columns
    assert isinstance(df_out, pd.DataFrame)
    assert len(df_out.columns) == 28
    
    # Check specific values
    assert df_out.loc[0, 'age_numeric'] == 52.0
    assert df_out.loc[0, 'sex'] == "Female"
    assert df_out.loc[0, 'cancer_site'] == "Breast"
    assert df_out.loc[0, 'harmonized_grade'] == 3
    assert df_out.loc[0, 'harmonized_stage'] == 2 # Regional is 2
    assert df_out.loc[0, 'node_ratio'] == 0.3
    assert df_out.loc[0, 'any_metastasis_at_dx'] == 1
    assert df_out.loc[0, 'treatment_intensity'] == 3 # Surgery + Chemo + Radiation
    assert df_out.loc[0, 'breast_receptor_subtype'] == "HR+/HER2-"

def test_seer_feature_engineer_missing_columns():
    engineer = SeerFeatureEngineer()
    
    # Missing columns should not crash and should use fallbacks
    minimal_patient = {
        "cancer_site": "Lung and Bronchus",
        "age_group": "30-34 years"
    }
    
    df_out = engineer.transform(minimal_patient)
    
    assert isinstance(df_out, pd.DataFrame)
    assert len(df_out.columns) == 28
    assert df_out.loc[0, 'age_numeric'] == 32.0
    assert df_out.loc[0, 'cancer_site'] == "Lung and Bronchus"
    assert df_out.loc[0, 'sex'] == "Unknown"
    assert df_out.loc[0, 'tumor_size_mm'] == -1.0
    assert df_out.loc[0, 'node_ratio'] == -1.0
