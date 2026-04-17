from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service
    service_name: str = "prediction-service"
    
    # Model paths (REAL MODEL)
    model_path: str = "../../ml-pipeline/models/rsf_seer_v1.pkl"
    encoders_path: str = "../../ml-pipeline/models/rsf_seer_v1_encoders.pkl"
    feature_names_path: str = "../../ml-pipeline/models/rsf_seer_v1_feature_names.pkl"
    metadata_path: str = "../../ml-pipeline/models/rsf_seer_v1_metadata.json"
    model_version: str = "rsf_seer_v1.0.0"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_model_cache_ttl: int = 86400  # 24 hours
    
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "cancer_db"
    db_user: str = "cancer_user"
    db_password: str = "dev_password_123"
    
    class Config:
        env_file = ".env"


settings = Settings()

