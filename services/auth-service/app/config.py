from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service
    service_name: str = "auth-service"
    
    # JWT
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15  # 15 minutes
    jwt_refresh_token_expire_days: int = 7     # 7 days
    
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "cancer_db"
    db_user: str = "cancer_user"
    db_password: str = "dev_password_123"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    class Config:
        env_file = ".env"


settings = Settings()

