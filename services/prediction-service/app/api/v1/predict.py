from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.inference.predictor import predict_recurrence
from app.db.database import get_db
from app.db.models import PredictionHistory
from app.auth import get_current_user
from datetime import datetime
import uuid
try:
    from constants import (
        CancerSite, AgeGroup, Sex, TumorGrade, HarmonizedStage, 
        HistologyBroad, Laterality, LVIStatus, RadiationType, 
        SurgRadSequence, BiomarkerStatus, MaritalStatus, IncomeLevel, RuralUrban
    )
except ImportError:
    # Fallback for different environments
    try:
        from shared_transformers.constants import (
            CancerSite, AgeGroup, Sex, TumorGrade, HarmonizedStage, 
            HistologyBroad, Laterality, LVIStatus, RadiationType, 
            SurgRadSequence, BiomarkerStatus, MaritalStatus, IncomeLevel, RuralUrban
        )
    except ImportError:
        pass

router = APIRouter()


class PredictRequest(BaseModel):
    cancer_site: CancerSite
    age_group: AgeGroup
    sex: Sex
    tumor_grade: TumorGrade
    harmonized_stage: HarmonizedStage
    tumor_size_mm: int = Field(..., ge=-1, le=500)
    histology_broad: HistologyBroad
    laterality: Laterality
    nodes_positive: int = Field(..., ge=-1, le=100)
    nodes_examined: int = Field(..., ge=-1, le=100)
    mets_bone: bool
    mets_liver: bool
    mets_lung: bool
    mets_brain: bool
    lvi: LVIStatus
    surgery_performed: bool
    radiation_type: RadiationType
    chemotherapy: bool
    surgery_radiation_sequence: SurgRadSequence
    days_to_treatment: str
    er_status: BiomarkerStatus
    pr_status: BiomarkerStatus
    her2_status: BiomarkerStatus
    marital_status: MaritalStatus
    income_level: IncomeLevel
    rural_urban: RuralUrban

    query_years: int = Field(default=5, ge=1, le=20)


class PredictResponse(BaseModel):
    prediction_id: str
    probability_pct: float
    risk_level: str
    interpretation: str
    model_version: str
    survival_curve: list[dict]
    timestamp: str


@router.post("", response_model=PredictResponse)
async def predict(
    request: PredictRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Run cancer recurrence prediction
    
    Input: 28-feature vector from Feature Service + query_years
    Output: Recurrence probability, risk level, interpretation
    """
    try:
        # Convert payload to dict for model
        feature_dict = request.model_dump(exclude={"query_years"}, mode='json')
        
        # Run prediction
        result = predict_recurrence(
            feature_dict=feature_dict,
            query_years=request.query_years
        )
        
        # Generate prediction ID
        prediction_id = str(uuid.uuid4())
        
        # Save to database
        db_history = PredictionHistory(
            prediction_id=prediction_id,
            user_id=user_id,
            feature_vector=feature_dict,  # Stores as JSONB
            probability=result["probability_pct"],
            risk_level=result["risk_level"],
            model_version=result["model_version"]
        )
        db.add(db_history)
        await db.commit()
        
        return PredictResponse(
            prediction_id=prediction_id,
            probability_pct=result["probability_pct"],
            risk_level=result["risk_level"],
            interpretation=result["interpretation"],
            model_version=result["model_version"],
            survival_curve=result["survival_curve"],
            timestamp=datetime.utcnow().isoformat()
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


class HistoryItem(BaseModel):
    prediction_id: str
    created_at: str
    probability_pct: float
    risk_level: str
    model_version: str


@router.get("/history", response_model=list[HistoryItem])
async def get_history(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PredictionHistory)
        .where(PredictionHistory.user_id == user_id)
        .order_by(PredictionHistory.created_at.desc())
    )
    records = result.scalars().all()
    
    return [
        HistoryItem(
            prediction_id=str(r.prediction_id),
            created_at=r.created_at.isoformat(),
            probability_pct=r.probability,
            risk_level=r.risk_level,
            model_version=r.model_version
        )
        for r in records
    ]


@router.get("/health")
async def health():
    """Health check endpoint"""
    from app.inference.model_loader import model_loader
    
    # Check if model is loaded
    model_status = "loaded" if model_loader.model is not None else "not_loaded"
    
    return {
        "status": "healthy",
        "service": "prediction-service",
        "model_version": model_loader.model_version,
        "model_status": model_status
    }


    