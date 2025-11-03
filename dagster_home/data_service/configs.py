from pydantic_settings import BaseSettings, SettingsConfigDict

class Configs(BaseSettings):
    CHALLENGER_ENDPOINT: str = "lol/league/v4/challengerleagues/by-queue/{queue}"
    MATCH_IDS_ENDPOINT: str = "lol/match/v5/matches/by-puuid/{puuid}/ids"
    MATCH_DATA_ENDPOINT: str = "lol/match/v5/matches/{match_id}"
    # Queue types
    SOLO_QUEUE: str = "RANKED_SOLO_5x5"

    # PIPELINE RUN_TIME
    RUNTIME: str = "20 3 * * *"
configs = Configs()
