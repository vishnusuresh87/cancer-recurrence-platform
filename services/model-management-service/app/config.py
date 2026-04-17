from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        protected_namespaces=("settings_",)
    )

    # Service
    service_name: str = "model-management-service"
    
    # Database
    db_host: str = "localhost"
    db_port: int = 55432
    db_name: str = "cancer_db"
    db_user: str = "cancer_user"
    db_password: str = "dev_password_123"
    
    # Local model storage (replaces GCS for dev)
    model_storage_path: str = "../../ml-pipeline/models"
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()

