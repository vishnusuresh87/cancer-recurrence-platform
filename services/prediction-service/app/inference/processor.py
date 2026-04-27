import pandas as pd
import numpy as np
from app.inference.model_loader import model_loader


class FeatureProcessor:
    """
    Transforms raw frontend features into the 28-feature numeric vector
    expected by the Random Survival Forest model.

    Model was trained with FEATURE_COLUMNS = [
        'age_numeric', 'sex', 'cancer_site', 'harmonized_grade', 'harmonized_stage',
        'tumor_size_mm', 'histology_code', 'laterality', 'nodes_positive', 'node_ratio',
        'any_metastasis_at_dx', 'mets_bone', 'mets_liver', 'mets_lung', 'mets_brain',
        'lvi', 'surgery_performed', 'radiation_type', 'chemotherapy_binary',
        'treatment_intensity', 'surgery_radiation_sequence', 'days_to_treatment',
        'er_status', 'pr_status', 'her2_status', 'breast_receptor_subtype',
        'marital_status', 'income_level'
    ]
    Note: 'rural_urban' is NOT in the model – it's a demographic field only.
    """

    AGE_MAPPING = {
        '00 years': 0, '01-04 years': 2.5, '05-09 years': 7, '10-14 years': 12,
        '15-19 years': 17, '20-24 years': 22, '25-29 years': 27, '30-34 years': 32,
        '35-39 years': 37, '40-44 years': 42, '45-49 years': 47, '50-54 years': 52,
        '55-59 years': 57, '60-64 years': 62, '65-69 years': 67, '70-74 years': 72,
        '75-79 years': 77, '80-84 years': 82, '85+ years': 87,
    }

    STAGE_MAPPING = {'In situ': 0, 'Localized': 1, 'Regional': 2, 'Distant': 3}

    GRADE_MAPPING = {
        'Grade I': 1, 'Well differentiated': 1,
        'Grade II': 2, 'Moderately differentiated': 2,
        'Grade III': 3, 'Poorly differentiated': 3,
        'Grade IV': 4, 'Undifferentiated': 4,
    }

    DAYS_TO_TREATMENT_MAPPING = {
        '0-30 days': 15, '31-90 days': 60, '91+ days': 120, 'Unknown': 45,
    }

    # histology_code in training was a RAW NUMERIC ICD-O-3 integer column (e.g. 8500, 8140).
    # It has NO LabelEncoder. Map the frontend broad string labels -> numeric ICD-O-3 codes.
    HISTOLOGY_BROAD_TO_CODE = {
        'Adenocarcinoma':          8140.0,   # NOS adenocarcinoma
        'Squamous cell carcinoma': 8070.0,   # Squamous cell carcinoma NOS
        'Ductal carcinoma':        8500.0,   # Infiltrating duct carcinoma
        'Lobular carcinoma':       8520.0,   # Lobular carcinoma NOS
        'Small cell carcinoma':    8041.0,   # Small cell carcinoma NOS
        'Large cell carcinoma':    8012.0,   # Large cell carcinoma NOS
        'Other':                   8000.0,   # Neoplasm malignant NOS
        'Unknown':                 8000.0,
    }

    def process(self, raw_data: dict) -> np.ndarray:
        """
        Main entry point: dict -> 1x28 numeric array
        """
        # 1. Start with raw features
        df = pd.DataFrame([raw_data])

        # 2. Synthesize engineered features

        # age_numeric
        df['age_numeric'] = df['age_group'].map(self.AGE_MAPPING).fillna(50)

        # harmonized_stage (map string -> int; input field is 'harmonized_stage')
        df['harmonized_stage'] = df['harmonized_stage'].map(self.STAGE_MAPPING).fillna(-1).astype(int)

        # harmonized_grade (derived from 'tumor_grade' input field)
        df['harmonized_grade'] = df['tumor_grade'].map(self.GRADE_MAPPING).fillna(-1).astype(int)

        # node_ratio
        df['nodes_examined'] = pd.to_numeric(df['nodes_examined'], errors='coerce').fillna(0)
        df['nodes_positive'] = pd.to_numeric(df['nodes_positive'], errors='coerce').fillna(0)
        df['node_ratio'] = np.where(
            df['nodes_examined'] > 0,
            df['nodes_positive'] / df['nodes_examined'],
            -1
        )

        # BUG FIX 1: Convert boolean fields to int BEFORE any bitwise OR
        # (JSON booleans come through as Python bool, which is fine, but
        #  explicit cast avoids subtle dtype issues on some pandas versions)
        for col in ['mets_bone', 'mets_liver', 'mets_lung', 'mets_brain', 'surgery_performed', 'chemotherapy']:
            if col in df.columns:
                df[col] = df[col].astype(int)

        # any_metastasis_at_dx
        df['any_metastasis_at_dx'] = (
            df['mets_bone'] | df['mets_liver'] | df['mets_lung'] | df['mets_brain']
        ).astype(int)

        # treatment components
        # The model was trained with column name 'chemotherapy_binary'
        df['chemotherapy_binary'] = df['chemotherapy']   # already cast to int above
        df['radiation_binary'] = (df['radiation_type'] != 'None').astype(int)
        df['surgery_performed_binary'] = df['surgery_performed']   # already cast to int above

        df['treatment_intensity'] = (
            df['surgery_performed_binary'] +
            df['chemotherapy_binary'] +
            df['radiation_binary']
        ).astype(int)

        # breast_receptor_subtype
        df['breast_receptor_subtype'] = df.apply(self._derive_breast_subtype, axis=1)

        # histology_code in training was a raw numeric ICD-O-3 integer column.
        # There is NO LabelEncoder for it — map broad string -> representative numeric code.
        broad_val = str(df['histology_broad'].iloc[0])
        histo_code = self.HISTOLOGY_BROAD_TO_CODE.get(broad_val, 8000.0)
        if broad_val not in self.HISTOLOGY_BROAD_TO_CODE:
            print(f"⚠️  histology_broad '{broad_val}' not in mapping, defaulting to 8000 (NOS).")
        df['histology_code'] = histo_code

        # BUG FIX 3: days_to_treatment – map bucketed strings to numeric midpoints
        # (the training pipeline stored numeric values; the frontend sends bucket labels)
        df['days_to_treatment'] = df['days_to_treatment'].map(
            self.DAYS_TO_TREATMENT_MAPPING
        ).fillna(45)

        # tumor_size_mm – ensure numeric
        df['tumor_size_mm'] = pd.to_numeric(df['tumor_size_mm'], errors='coerce').fillna(30.0)

        # 3. Encoding Categorical Features
        encoders = model_loader.get_encoders()
        feature_order = model_loader.get_feature_names()

        # Work on a fresh copy so we don't mutate the input
        processed_df = df.copy()

        # Categorical columns must be strings for the LabelEncoders
        for col in encoders:
            if col in processed_df.columns:
                processed_df[col] = processed_df[col].astype(str)

        # Apply label encoders – with graceful unknown-category handling
        for col, le in encoders.items():
            if col in processed_df.columns:
                val = processed_df[col].iloc[0]
                if val not in le.classes_:
                    fallback = 'Unknown' if 'Unknown' in le.classes_ else le.classes_[0]
                    print(f"⚠️  Column '{col}': Category '{val}' unknown. Using '{fallback}'.")
                    val = fallback
                processed_df[col] = le.transform([val])[0]

        # 4. Final selection and ordering
        try:
            missing = set(feature_order) - set(processed_df.columns)
            if missing:
                raise ValueError(f"Missing features required by model: {missing}")

            # BUG FIX 4: Use .copy() to avoid SettingWithCopyWarning and silent failures
            X_df = processed_df[feature_order].copy()

            for col in feature_order:
                try:
                    X_df[col] = pd.to_numeric(X_df[col])
                except Exception as e:
                    print(f"❌ Column '{col}' cannot be converted to numeric. "
                          f"Value: '{X_df[col].iloc[0]}'. "
                          f"Was it encoded? Encoders cover: {list(encoders.keys())}")
                    raise ValueError(f"Feature conversion failed for '{col}': {str(e)}")

            return X_df.values.astype(np.float64)

        except KeyError as e:
            missing = set(feature_order) - set(processed_df.columns)
            raise ValueError(f"Missing essential features for model: {missing}") from e

    def _derive_breast_subtype(self, row):
        if row.get('cancer_site') != 'Breast':
            return 'Not Breast Cancer'

        er = row.get('er_status', 'Unknown')
        pr = row.get('pr_status', 'Unknown')
        her2 = row.get('her2_status', 'Unknown')

        er_pos = er == 'Positive'
        pr_pos = pr == 'Positive'
        her2_pos = her2 == 'Positive'

        if (er_pos or pr_pos) and her2_pos:       return 'HR+/HER2+'
        elif (er_pos or pr_pos) and not her2_pos:  return 'HR+/HER2-'
        elif not (er_pos or pr_pos) and her2_pos:  return 'HR-/HER2+'
        else:                                       return 'Triple Negative'


# Global instance
feature_processor = FeatureProcessor()
