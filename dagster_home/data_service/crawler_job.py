from dagster_home.data_service.utils.common import request_riot_api
from dagster_home.data_service.configs import configs
from settings import settings
from datetime import datetime
from typing import Dict, List
from dagster_home.data_service.utils.db_operator import S3Operator
from loguru import logger

class RiotAPIClient:
    def __init__(self, regions: list[str]):
        self.regions = regions
        self.s3_operator = S3Operator(
            endpoint=settings.S3_ENDPOINT,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            bucket_name=settings.S3_DATA_BUCKET
        )

    def fetch_challenger_data(self):
        results = {}
        for region in self.regions:
            try:
                resp = request_riot_api(
                    region=region,
                    endpoint=configs.CHALLENGER_ENDPOINT.format(queue=configs.SOLO_QUEUE)
                )
                results[region] = resp
                logger.info(f"Fetched {region}")
            except Exception as e:
                logger.error(f"Fetch failed {region}: {e}")
                results[region] = None
        return results

    def process_challenger_data(self, challenger_data: Dict) -> List[str]:
        processed = []
        ts = datetime.now().isoformat()
        for region, league_data in challenger_data.items():
            if not league_data or 'entries' not in league_data:
                logger.warning(f"No entries {region}")
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
                    'veteran': bool(entry.get('veteran')) if entry.get('veteran') is not None else False,
                    'inactive': bool(entry.get('inactive')) if entry.get('inactive') is not None else False,
                    'fresh_blood': bool(entry.get('freshBlood')) if entry.get('freshBlood') is not None else False,
                    'hot_streak': bool(entry.get('hotStreak')) if entry.get('hotStreak') is not None else False,
                    'last_updated': str(ts)
                }
                key = f"players/region={region}/{puuid}.json"
                ok = self.s3_operator.upload_json(
                    key=key,
                    data=player_data,
                )
                if ok:
                    processed.append(puuid)
                logger.debug(player_data)
        logger.info(f"Processed {len(processed)}")
        return processed

if __name__ == "__main__":
    client = RiotAPIClient(regions=settings.SUPPORTED_REGIONS)
    data = client.fetch_challenger_data()
    client.process_challenger_data(data)
