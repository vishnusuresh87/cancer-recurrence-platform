from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.inference.predictor import predict_recurrence
from datetime import datetime
import uuid

router = APIRouter()


class PredictRequest(BaseModel):
    feature_vector: list[float] = Field(..., min_length=28, max_length=28)
    query_years: int = Field(default=5, ge=1, le=20)


class PredictResponse(BaseModel):
    prediction_id: str
    probability_pct: float
    risk_level: str
    interpretation: str
    model_version: str
    survival_curve: list[dict]
    timestamp: str


@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Run cancer recurrence prediction
    
    Input: 28-feature vector from Feature Service + query_years
    Output: Recurrence probability, risk level, interpretation
    """
    try:
        # Run prediction
        result = predict_recurrence(
            feature_vector=request.feature_vector,
            query_years=request.query_years
        )
        
        # Generate prediction ID
        prediction_id = str(uuid.uuid4())
        
        # TODO: Save to database (prediction_history table)
        # This will be added when we integrate with database
        
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


    