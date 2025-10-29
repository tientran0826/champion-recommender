from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    RIOT_API_KEY: str
    SUPPORTED_REGIONS: list[str] = ["EUN1", "EUW1", "JP1", "KR", "LA1", "NA1", "VN2"]
    BASE_RIOT_API_URL: str = "api.riotgames.com"

    # Queue types
    SOLO_QUEUE: str = "RANKED_SOLO_5x5"

settings = Settings()
print(settings.RIOT_API_KEY)
