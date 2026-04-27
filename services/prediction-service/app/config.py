from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service
    service_name: str = "prediction-service"
    # JWT
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"

    # Model paths (REAL MODEL)
    model_path: str = "../../ml-pipeline/models/rsf_seer_v1.pkl"
    encoders_path: str = "../../ml-pipeline/models/rsf_seer_v1_encoders.pkl"
    feature_names_path: str = "../../ml-pipeline/models/rsf_seer_v1_feature_names.pkl"
    metadata_path: str = "../../ml-pipeline/models/rsf_seer_v1_metadata.json"
    model_version: str = "rsf_seer_v1.0.0"
    
    # Redis
    redis_host: str
    redis_port: int
    redis_model_cache_ttl: int = 86400  # 24 hours
    
    # Internal Service Coordination
    model_management_url: str
    model_poll_interval: int = 21600  # 6 hours in seconds
    
    # Database
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    
    model_config = {
        "protected_namespaces": (),
        "env_file": ".env"
    }

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()

