import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
try:
    from ..constants import AgeGroup, TumorGrade, HarmonizedStage, BiomarkerStatus
except (ImportError, ValueError):
    from constants import AgeGroup, TumorGrade, HarmonizedStage, BiomarkerStatus

class SeerFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Scikit-Learn Custom Transformer to apply business logic to raw SEER or frontend data.
    Ensures Train-Serve skew is impossible by using this inside the ML Pipeline.
    """
    
    def __init__(self):
        # We output exactly the 28 columns required by the model in order
        self.feature_columns = [
            'age_numeric', 'sex', 'cancer_site', 'harmonized_grade', 'harmonized_stage',
            'tumor_size_mm', 'histology_code', 'laterality', 'nodes_positive', 'node_ratio',
            'any_metastasis_at_dx', 'mets_bone', 'mets_liver', 'mets_lung', 'mets_brain',
            'lvi', 'surgery_performed', 'radiation_type', 'chemotherapy_binary', 'treatment_intensity',
            'surgery_radiation_sequence', 'days_to_treatment', 'er_status', 'pr_status', 'her2_status',
            'breast_receptor_subtype', 'marital_status', 'income_level',
        ]

    def fit(self, X, y=None):
        return self

    def _get_series(self, df, col, default_val):
        if col in df.columns:
            return df[col]
        return pd.Series(default_val, index=df.index)

    def transform(self, X):
        # Ensure working on a copy
        df = X.copy()
        if isinstance(df, dict):
            df = pd.DataFrame([df])
            
        out = pd.DataFrame(index=df.index)
        
        # 1. age_numeric
        age_mapping = {
            AgeGroup.YEARS_00.value: 0, 
            AgeGroup.YEARS_01_04.value: 2.5, 
            AgeGroup.YEARS_05_09.value: 7, 
            AgeGroup.YEARS_10_14.value: 12, 
            AgeGroup.YEARS_15_19.value: 17, 
            AgeGroup.YEARS_20_24.value: 22,
            AgeGroup.YEARS_25_29.value: 27, 
            AgeGroup.YEARS_30_34.value: 32, 
            AgeGroup.YEARS_35_39.value: 37,
            AgeGroup.YEARS_40_44.value: 42, 
            AgeGroup.YEARS_45_49.value: 47, 
            AgeGroup.YEARS_50_54.value: 52,
            AgeGroup.YEARS_55_59.value: 57, 
            AgeGroup.YEARS_60_64.value: 62, 
            AgeGroup.YEARS_65_69.value: 67,
            AgeGroup.YEARS_70_74.value: 72, 
            AgeGroup.YEARS_75_79.value: 77, 
            AgeGroup.YEARS_80_84.value: 82,
            AgeGroup.YEARS_85_PLUS.value: 87,
        }
        out['age_numeric'] = self._get_series(df, 'age_group', '').map(age_mapping).fillna(50.0).astype(float)
        
        # 2-3. Pass through
        out['sex'] = self._get_series(df, 'sex', 'Unknown')
        out['cancer_site'] = self._get_series(df, 'cancer_site', 'Unknown')
        
        # 4. harmonized_grade
        def map_grade(v):
            if not isinstance(v, str): return -1
            v_lower = v.lower()
            if 'grade i' in v_lower or 'well' in v_lower: return 1
            if 'grade ii' in v_lower or 'moderately' in v_lower: return 2
            if 'grade iii' in v_lower or 'poorly' in v_lower: return 3
            if 'grade iv' in v_lower or 'undifferentiated' in v_lower: return 4
            return -1
        out['harmonized_grade'] = self._get_series(df, 'tumor_grade', '').apply(map_grade).astype(int)
        
        # 5. harmonized_stage
        def map_stage(v):
            if not isinstance(v, str): return -1
            if v == HarmonizedStage.IN_SITU.value: return 0
            if v == HarmonizedStage.LOCALIZED.value: return 1
            if v == HarmonizedStage.REGIONAL.value: return 2
            if v == HarmonizedStage.DISTANT.value: return 3
            return -1
        # Frontend provides "harmonized_stage" directly as string Localized/Regional etc
        stage_col = df['harmonized_stage'] if 'harmonized_stage' in df.columns else (df['summary_stage'] if 'summary_stage' in df.columns else pd.Series('', index=df.index))
        out['harmonized_stage'] = stage_col.apply(map_stage).astype(int)
        
        # 6-9. Numeric/Pass-through
        out['tumor_size_mm'] = pd.to_numeric(self._get_series(df, 'tumor_size_mm', -1), errors='coerce').fillna(-1).astype(float)
        hist_col = df['histology_broad'] if 'histology_broad' in df.columns else (df['histology_code'] if 'histology_code' in df.columns else pd.Series('Unknown', index=df.index))
        out['histology_code'] = hist_col.astype(str)
        out['laterality'] = self._get_series(df, 'laterality', 'Unknown').astype(str)
        out['nodes_positive'] = pd.to_numeric(self._get_series(df, 'nodes_positive', -1), errors='coerce').fillna(-1).astype(float)
        
        # 10. node_ratio
        nodes_pos = pd.to_numeric(self._get_series(df, 'nodes_positive', -1), errors='coerce').fillna(-1)
        nodes_exam = pd.to_numeric(self._get_series(df, 'nodes_examined', -1), errors='coerce').fillna(-1)
        # Using numpy where for vectorized conditions
        out['node_ratio'] = np.where(nodes_exam > 0, nodes_pos / nodes_exam, -1.0)
        
        # 11-15. Metastasis 
        mets_bone = self._get_series(df, 'mets_bone', False).astype(bool)
        mets_liver = self._get_series(df, 'mets_liver', False).astype(bool)
        mets_lung = self._get_series(df, 'mets_lung', False).astype(bool)
        mets_brain = self._get_series(df, 'mets_brain', False).astype(bool)
        
        out['any_metastasis_at_dx'] = (mets_bone | mets_liver | mets_lung | mets_brain).astype(int)
        out['mets_bone'] = mets_bone.astype(int)
        out['mets_liver'] = mets_liver.astype(int)
        out['mets_lung'] = mets_lung.astype(int)
        out['mets_brain'] = mets_brain.astype(int)
        
        # 16-19.
        out['lvi'] = self._get_series(df, 'lvi', 'Unknown').astype(str)
        out['surgery_performed'] = self._get_series(df, 'surgery_performed', False).astype(int)
        out['radiation_type'] = self._get_series(df, 'radiation_type', 'None').astype(str)
        out['chemotherapy_binary'] = self._get_series(df, 'chemotherapy', False).astype(int)
        
        # 20. treatment_intensity
        rad_intensity = (out['radiation_type'] != 'None').astype(int)
        out['treatment_intensity'] = out['surgery_performed'] + out['chemotherapy_binary'] + rad_intensity
        
        # 21-25.
        out['surgery_radiation_sequence'] = self._get_series(df, 'surgery_radiation_sequence', 'Unknown').astype(str)
        out['days_to_treatment'] = self._get_series(df, 'days_to_treatment', 'Unknown').astype(str)
        out['er_status'] = self._get_series(df, 'er_status', 'Unknown').astype(str)
        out['pr_status'] = self._get_series(df, 'pr_status', 'Unknown').astype(str)
        out['her2_status'] = self._get_series(df, 'her2_status', 'Unknown').astype(str)
        
        # 26. breast_receptor_subtype
        def derive_subtype(row):
            site = str(row.get('cancer_site', ''))
            if 'Breast' not in site:
                return 'Not Breast Cancer'
            er = str(row.get('er_status', ''))
            pr = str(row.get('pr_status', ''))
            her2 = str(row.get('her2_status', ''))
            
            hr_pos = (er == BiomarkerStatus.POSITIVE.value) or (pr == BiomarkerStatus.POSITIVE.value)
            her2_pos = (her2 == BiomarkerStatus.POSITIVE.value)
            hr_neg = (er == BiomarkerStatus.NEGATIVE.value) and (pr == BiomarkerStatus.NEGATIVE.value)
            her2_neg = (her2 == BiomarkerStatus.NEGATIVE.value)
            
            if hr_pos and her2_pos: return 'HR+/HER2+'
            if hr_pos and her2_neg: return 'HR+/HER2-'
            if hr_neg and her2_pos: return 'HR-/HER2+'
            if hr_neg and her2_neg: return 'Triple Negative'
            return 'Unknown'
            
        out['breast_receptor_subtype'] = df.apply(derive_subtype, axis=1)
        
        # 27-28.
        out['marital_status'] = self._get_series(df, 'marital_status', 'Unknown').astype(str)
        out['income_level'] = self._get_series(df, 'income_level', 'Unknown').astype(str)
        
        return out[self.feature_columns]
