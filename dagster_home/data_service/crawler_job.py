import time
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger
from dagster_home.data_service.utils.common import request_riot_api
from dagster_home.data_service.configs import configs
from settings import settings
from dagster_home.data_service.utils.db_operator import S3Operator


def retry_request(func, max_retries=5, backoff=5, **kwargs):
    """
    Generic retry wrapper with exponential backoff.
    Retries on rate limit, connection errors, and unexpected failures.
    """
    for attempt in range(1, max_retries + 1):
        try:
            return func(**kwargs)
        except Exception as e:
            err_msg = str(e)
            # Riot rate limit → status code 429
            if "429" in err_msg or "rate limit" in err_msg.lower():
                wait_time = backoff * attempt
                logger.warning(f"Rate limit hit. Waiting {wait_time}s before retry {attempt}/{max_retries}...")
                time.sleep(wait_time)
            else:
                logger.warning(f"Request failed (attempt {attempt}/{max_retries}): {e}")
                time.sleep(backoff)

    logger.error(f"Request permanently failed after {max_retries} attempts.")
    return None


class RiotAPIClient:
    def __init__(self, regions: list[str]):
        self.regions = regions
        self.s3_operator = S3Operator(
            endpoint=settings.S3_ENDPOINT,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            bucket_name=settings.S3_DATA_BUCKET
        )

    # ----------------- Challenger Data -----------------
    def fetch_challenger_data(self):
        results = {}
        for region in self.regions:
            resp = retry_request(
                request_riot_api,
                region=region,
                endpoint=configs.CHALLENGER_ENDPOINT.format(queue=configs.SOLO_QUEUE)
            )
            if resp:
                logger.info(f"Fetched challenger for {region}")
            else:
                logger.error(f"Failed challenger data for {region}")
            results[region] = resp
        return results

    def process_challenger_data(self, challenger_data: Dict) -> List[str]:
        processed = []
        ts = datetime.now().isoformat()

        for region, league_data in challenger_data.items():
            if not league_data or 'entries' not in league_data:
                logger.warning(f"No entries for region={region}")
                continue

            for entry in league_data['entries']:
                puuid = entry.get('puuid')
                if not puuid:
                    continue

                player_data = {
                    'puuid': str(puuid),
                    'tier': str(league_data.get('tier', '')),
                    'queue': str(league_data.get('queue', '')),
                    'league_id': str(league_data.get('leagueId', '')),
                    'league_name': str(league_data.get('name', '')),
                    'rank': str(entry.get('rank', '')),
                    'league_points': int(entry.get('leaguePoints', 0)),
                    'wins': int(entry.get('wins', 0)),
                    'losses': int(entry.get('losses', 0)),
                    'veteran': bool(entry.get('veteran')),
                    'inactive': bool(entry.get('inactive')),
                    'fresh_blood': bool(entry.get('freshBlood')),
                    'hot_streak': bool(entry.get('hotStreak')),
                    'last_updated': ts,
                }

                key = f"raw/players/region={region}/{puuid}.json"
                if self.s3_operator.upload_json(key=key, data=player_data):
                    processed.append(puuid)

        logger.info(f"Processed {len(processed)} challenger players")
        return processed

    # ----------------- Match IDs -----------------
    def fetch_match_ids_by_puuid(self, puuid: str) -> List[str]:
        endpoint = configs.MATCH_IDS_ENDPOINT.format(puuid=puuid)
        resp = retry_request(
            request_riot_api,
            region='ASIA',
            endpoint=endpoint,
            params={"start": 0, "count": 20}
        )
        if resp:
            logger.info(f"Fetched match IDs for {puuid}")
        else:
            return []
        return resp

    # ----------------- Match Data -----------------
    def fetch_match_data(self, match_id: str) -> Dict:
        resp = retry_request(
            request_riot_api,
            region='ASIA',
            endpoint=configs.MATCH_DATA_ENDPOINT.format(match_id=match_id)
        )
        if not resp:
            logger.error(f"Failed match data {match_id}")
            return {}
        return resp

    def process_match_data(self, match_data: Dict):
        match_id = match_data.get('metadata', {}).get('matchId', 'unknown')
        key = f"raw/matches/{match_id}.json"
        if self.s3_operator.upload_json(key=key, data=match_data):
            logger.info(f"Saved match {match_id}")
        else:
            logger.error(f"Failed to save match {match_id}")
