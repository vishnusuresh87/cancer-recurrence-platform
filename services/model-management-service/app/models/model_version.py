from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Enum as SQLEnum
from datetime import datetime
import enum
from app.database import Base


class ModelStatus(str, enum.Enum):
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    FAILED = "failed"


class ModelVersion(Base):
    __tablename__ = "model_versions"
    
    version = Column(String(50), primary_key=True)
    storage_path = Column(String(500), nullable=False)  # Local path or GCS path
    status = Column(SQLEnum(ModelStatus, name="model_status", values_callable=lambda x: [e.value for e in x]), default=ModelStatus.STAGING, nullable=False)
    metrics = Column(JSON, nullable=True)  # {"c_index": 0.78, "brier_score": 0.12}
    training_date = Column(DateTime, nullable=True)
    training_samples = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    promoted_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ModelVersion {self.version} ({self.status})>"