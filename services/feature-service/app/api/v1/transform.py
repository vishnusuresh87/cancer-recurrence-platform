from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import joblib
from pathlib import Path

router = APIRouter()

# Load encoders from trained model
ENCODERS_PATH = "../../ml-pipeline/models/rsf_seer_v1_encoders.pkl"
FEATURE_NAMES_PATH = "../../ml-pipeline/models/rsf_seer_v1_feature_names.pkl"

encoders = None
feature_names = None


def load_encoders():
    """Load encoders and feature names from trained model"""
    global encoders, feature_names
    
    if encoders is None:
        encoders_path = Path(ENCODERS_PATH)
        feature_names_path = Path(FEATURE_NAMES_PATH)
        
        if not encoders_path.exists():
            raise FileNotFoundError(f"Encoders not found: {encoders_path}")
        
        encoders = joblib.load(encoders_path)
        feature_names = joblib.load(feature_names_path)
        print(f"✅ Loaded {len(encoders)} encoders")
        print(f"✅ Loaded {len(feature_names)} feature names")


# Load on startup
load_encoders()


class TransformRequest(BaseModel):
    # Demographics
    cancer_site: str
    age_group: str
    sex: str
    
    # Tumor characteristics
    tumor_grade: str
    harmonized_stage: str
    tumor_size_mm: int
    histology_broad: str
    laterality: str
    
    # Nodes
    nodes_positive: int
    nodes_examined: int
    
    # Metastasis
    mets_bone: bool
    mets_liver: bool
    mets_lung: bool
    mets_brain: bool
    
    # Pathology
    lvi: str
    
    # Treatment
    surgery_performed: bool
    radiation_type: str
    chemotherapy: bool
    surgery_radiation_sequence: str
    days_to_treatment: str
    
    # Breast cancer specific
    er_status: str
    pr_status: str
    her2_status: str
    
    # Socioeconomic
    marital_status: str
    income_level: str
    rural_urban: str


class TransformResponse(BaseModel):
    feature_vector: list[float]
    feature_names: list[str]


@router.post("/transform", response_model=TransformResponse)
async def transform(request: TransformRequest):
    """
    Transform user inputs using SAME encoders as training
    """
    try:
        # Map age group to numeric
        age_mapping = {
            '00 years': 0,
            '01-04 years': 2.5,
            '05-09 years': 7,
            '10-14 years': 12,
            '15-19 years': 17,
            '20-24 years': 22,
            '25-29 years': 27,
            '30-34 years': 32,
            '35-39 years': 37,
            '40-44 years': 42,
            '45-49 years': 47,
            '50-54 years': 52,
            '55-59 years': 57,
            '60-64 years': 62,
            '65-69 years': 67,
            '70-74 years': 72,
            '75-79 years': 77,
            '80-84 years': 82,
            '85+ years': 87,
        }
        age_numeric = age_mapping.get(request.age_group, 50.0)
        
        # Calculate derived features
        node_ratio = (
            request.nodes_positive / request.nodes_examined
            if request.nodes_examined > 0 else -1.0
        )
        
        any_metastasis_at_dx = any([
            request.mets_bone,
            request.mets_liver,
            request.mets_lung,
            request.mets_brain
        ])
        
        treatment_intensity = (
            int(request.surgery_performed) +
            int(request.chemotherapy) +
            (0 if request.radiation_type == "None" else 1)
        )
        
        # Derive breast receptor subtype
        er = request.er_status
        pr = request.pr_status
        her2 = request.her2_status
        
        if "Positive" in er or "Positive" in pr:
            if "Positive" in her2:
                breast_subtype = "HR+/HER2+"
            else:
                breast_subtype = "HR+/HER2-"
        else:
            if "Positive" in her2:
                breast_subtype = "HR-/HER2+"
            else:
                breast_subtype = "Triple Negative"
        
        # Harmonize grade
        grade_mapping = {
            'Grade I': 1,
            'Well differentiated': 1,
            'Grade II': 2,
            'Moderately differentiated': 2,
            'Grade III': 3,
            'Poorly differentiated': 3,
            'Grade IV': 4,
            'Undifferentiated': 4,
        }
        harmonized_grade = grade_mapping.get(request.tumor_grade, -1)
        
        # Harmonize stage
        stage_mapping = {
            'In situ': 0,
            'Localized': 1,
            'Regional': 2,
            'Distant': 3,
        }
        harmonized_stage_num = stage_mapping.get(request.harmonized_stage, -1)
        
        # Build feature dictionary (in same order as training)
        features = {
            'age_numeric': age_numeric,
            'sex': request.sex,
            'cancer_site': request.cancer_site,
            'harmonized_grade': harmonized_grade,
            'harmonized_stage': harmonized_stage_num,
            'tumor_size_mm': float(request.tumor_size_mm),
            'histology_code': request.histology_broad,
            'laterality': request.laterality,
            'nodes_positive': float(request.nodes_positive),
            'node_ratio': node_ratio,
            'any_metastasis_at_dx': int(any_metastasis_at_dx),
            'mets_bone': int(request.mets_bone),
            'mets_liver': int(request.mets_liver),
            'mets_lung': int(request.mets_lung),
            'mets_brain': int(request.mets_brain),
            'lvi': request.lvi,
            'surgery_performed': int(request.surgery_performed),
            'radiation_type': request.radiation_type,
            'chemotherapy_binary': int(request.chemotherapy),
            'treatment_intensity': treatment_intensity,
            'surgery_radiation_sequence': request.surgery_radiation_sequence,
            'days_to_treatment': request.days_to_treatment,
            'er_status': request.er_status,
            'pr_status': request.pr_status,
            'her2_status': request.her2_status,
            'breast_receptor_subtype': breast_subtype,
            'marital_status': request.marital_status,
            'income_level': request.income_level,
        }
        
        # Apply encoders (same as training)
        feature_vector = []
        for feature_name in feature_names:
            value = features[feature_name]
            
            # If this feature has an encoder, apply it
            if feature_name in encoders:
                encoder = encoders[feature_name]
                try:
                    # Transform using fitted encoder
                    if value not in encoder.classes_:
                        # Unknown category - use -1
                        encoded_value = -1.0
                    else:
                        encoded_value = float(encoder.transform([value])[0])
                except:
                    encoded_value = -1.0
            else:
                # Numeric feature - use as-is
                try:
                    encoded_value = float(value)
                except ValueError:
                    encoded_value = -1.0
            
            feature_vector.append(encoded_value)
        
        return TransformResponse(
            feature_vector=feature_vector,
            feature_names=feature_names
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transformation failed: {str(e)}")


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "feature-service",
        "encoders_loaded": encoders is not None,
        "n_features": len(feature_names) if feature_names else 0
    }


