from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import json

from app.database import get_db
from app.models.model_version import ModelVersion, ModelStatus
from app.config import settings

router = APIRouter()


def _status_to_str(value) -> str:
    if isinstance(value, ModelStatus):
        return value.value
    return str(value)


def _dt_to_iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


# ==================== Schemas ====================

class ModelMetrics(BaseModel):
    c_index_train: Optional[float] = None
    c_index_test: Optional[float] = None
    brier_score: Optional[float] = None
    calibration_score: Optional[float] = None


class ModelVersionCreate(BaseModel):
    version: str = Field(..., pattern=r"^rsf_seer_v\d+\.\d+\.\d+$")
    storage_path: str
    metrics: Optional[ModelMetrics] = None
    training_samples: Optional[int] = None


class ModelVersionResponse(BaseModel):
    version: str
    storage_path: str
    status: str
    metrics: Optional[dict]
    training_date: Optional[str]
    training_samples: Optional[int]
    created_at: str
    promoted_at: Optional[str]


class PromoteRequest(BaseModel):
    traffic_percentage: int = Field(default=100, ge=1, le=100)


# ==================== Endpoints ====================

@router.post("/", response_model=ModelVersionResponse, status_code=status.HTTP_201_CREATED)
async def register_model(
    model: ModelVersionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new model version
    
    Flow:
    1. Train model with ml-pipeline/scripts/train_rsf_model.py
    2. POST to this endpoint to register it
    3. Model starts in 'staging' status
    4. Use /promote to move to production
    """
    # Check if version already exists
    result = await db.execute(
        select(ModelVersion).where(ModelVersion.version == model.version)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model version {model.version} already exists"
        )
    
    # Verify model file exists
    model_path = Path(model.storage_path)
    if not model_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model file not found at: {model.storage_path}"
        )
    
    # Create model version record
    new_model = ModelVersion(
        version=model.version,
        storage_path=model.storage_path,
        status=ModelStatus.STAGING,
        metrics=model.metrics.dict() if model.metrics else None,
        training_date=datetime.utcnow(),
        training_samples=model.training_samples
    )
    
    db.add(new_model)
    await db.commit()
    await db.refresh(new_model)
    
    return ModelVersionResponse(
        version=new_model.version,
        storage_path=new_model.storage_path,
        status=new_model.status.value,
        metrics=new_model.metrics,
        training_date=new_model.training_date.isoformat() if new_model.training_date else None,
        training_samples=new_model.training_samples,
        created_at=new_model.created_at.isoformat(),
        promoted_at=new_model.promoted_at.isoformat() if new_model.promoted_at else None
    )


@router.get("/", response_model=List[ModelVersionResponse])
async def list_models(
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all model versions
    
    Optional filter by status: staging, production, archived, failed
    """
    query = select(ModelVersion).order_by(desc(ModelVersion.created_at))
    
    if status_filter:
        try:
            status_enum = ModelStatus(status_filter)
            query = query.where(ModelVersion.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    
    try:
        result = await db.execute(query)
        models = result.scalars().all()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {exc.__class__.__name__}"
        )
    
    return [
        ModelVersionResponse(
            version=m.version,
            storage_path=m.storage_path,
            status=_status_to_str(m.status),
            metrics=m.metrics,
            training_date=_dt_to_iso(m.training_date),
            training_samples=m.training_samples,
            created_at=_dt_to_iso(m.created_at) or datetime.utcnow().isoformat(),
            promoted_at=_dt_to_iso(m.promoted_at)
        )
        for m in models
    ]


@router.get("/production", response_model=ModelVersionResponse)
async def get_production_model(db: AsyncSession = Depends(get_db)):
    """
    Get current production model
    """
    result = await db.execute(
        select(ModelVersion).where(ModelVersion.status == ModelStatus.PRODUCTION)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No production model found"
        )
    
    return ModelVersionResponse(
        version=model.version,
        storage_path=model.storage_path,
        status=model.status.value,
        metrics=model.metrics,
        training_date=model.training_date.isoformat() if model.training_date else None,
        training_samples=model.training_samples,
        created_at=model.created_at.isoformat(),
        promoted_at=model.promoted_at.isoformat() if model.promoted_at else None
    )


@router.post("/{version}/promote", response_model=ModelVersionResponse)
async def promote_to_production(
    version: str,
    promote_request: PromoteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Promote a staging model to production
    
    Steps:
    1. Archive current production model
    2. Promote specified model to production
    3. (Optional) Enable A/B testing with traffic_percentage < 100
    
    Note: A/B testing requires API Gateway configuration (Kong)
    """
    # Get model to promote
    result = await db.execute(
        select(ModelVersion).where(ModelVersion.version == version)
    )
    model_to_promote = result.scalar_one_or_none()
    
    if not model_to_promote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {version} not found"
        )
    
    if model_to_promote.status == ModelStatus.PRODUCTION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model {version} is already in production"
        )
    
    # Archive current production model(s)
    await db.execute(
        update(ModelVersion)
        .where(ModelVersion.status == ModelStatus.PRODUCTION)
        .values(
            status=ModelStatus.ARCHIVED,
            archived_at=datetime.utcnow()
        )
    )
    
    # Promote new model
    model_to_promote.status = ModelStatus.PRODUCTION
    model_to_promote.promoted_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(model_to_promote)
    
    # TODO: If traffic_percentage < 100, configure A/B testing in Kong
    # For now, we just promote to 100% traffic
    
    return ModelVersionResponse(
        version=model_to_promote.version,
        storage_path=model_to_promote.storage_path,
        status=model_to_promote.status.value,
        metrics=model_to_promote.metrics,
        training_date=model_to_promote.training_date.isoformat() if model_to_promote.training_date else None,
        training_samples=model_to_promote.training_samples,
        created_at=model_to_promote.created_at.isoformat(),
        promoted_at=model_to_promote.promoted_at.isoformat() if model_to_promote.promoted_at else None
    )


@router.post("/{version}/rollback", response_model=ModelVersionResponse)
async def rollback_model(
    version: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Rollback to a previous model version
    
    Use case: New model performs poorly, need to quickly revert
    """
    # Archive current production
    await db.execute(
        update(ModelVersion)
        .where(ModelVersion.status == ModelStatus.PRODUCTION)
        .values(
            status=ModelStatus.ARCHIVED,
            archived_at=datetime.utcnow()
        )
    )
    
    # Promote rollback version
    result = await db.execute(
        select(ModelVersion).where(ModelVersion.version == version)
    )
    rollback_model = result.scalar_one_or_none()
    
    if not rollback_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {version} not found"
        )
    
    rollback_model.status = ModelStatus.PRODUCTION
    rollback_model.promoted_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(rollback_model)
    
    return ModelVersionResponse(
        version=rollback_model.version,
        storage_path=rollback_model.storage_path,
        status=rollback_model.status.value,
        metrics=rollback_model.metrics,
        training_date=rollback_model.training_date.isoformat() if rollback_model.training_date else None,
        training_samples=rollback_model.training_samples,
        created_at=rollback_model.created_at.isoformat(),
        promoted_at=rollback_model.promoted_at.isoformat() if rollback_model.promoted_at else None
    )


@router.delete("/{version}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    version: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a model version (only if not in production)
    """
    result = await db.execute(
        select(ModelVersion).where(ModelVersion.version == version)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {version} not found"
        )
    
    if model.status == ModelStatus.PRODUCTION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete production model"
        )
    
    await db.delete(model)
    await db.commit()


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "model-management-service"}


