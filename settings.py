from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="./.env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    RIOT_API_KEY: str
    SUPPORTED_REGIONS: list[str] = ["KR"]
    BASE_RIOT_API_URL: str = "api.riotgames.com"

    # Queue types
    SOLO_QUEUE: str = "RANKED_SOLO_5x5"

    # S3 Configuration
    S3_ENDPOINT: str = "minio:9000"
    S3_ACCESS_KEY: str = "admin"
    S3_SECRET_KEY: str = "admin1234"
    S3_DATA_BUCKET: str = "data-lakehouse"

settings = Settings()
