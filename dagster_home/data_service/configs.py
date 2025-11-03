from pydantic_settings import BaseSettings, SettingsConfigDict

class Configs(BaseSettings):
    CHALLENGER_ENDPOINT: str = "lol/league/v4/challengerleagues/by-queue/{queue}"
    # Queue types
    SOLO_QUEUE: str = "RANKED_SOLO_5x5"

configs = Configs()
