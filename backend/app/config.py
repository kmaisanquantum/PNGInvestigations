from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://investigator:investigator@postgres:5432/investigations"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8
    evidence_storage_path: str = "/data/evidence"
    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
