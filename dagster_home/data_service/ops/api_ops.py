import time
from dagster import op
from dagster_home.data_service.crawler_job import RiotAPIClient
from settings import settings
from loguru import logger

@op
def fetch_challenger_data(context):
    client = RiotAPIClient(regions=settings.SUPPORTED_REGIONS)
    data = client.fetch_challenger_data()
    processed_puuids = client.process_challenger_data(data)

    # Use Dagster's context logger
    context.log.info(f"Processed {len(processed_puuids)} players")

    return processed_puuids

@op
def fetch_match_data_by_puuids(context, puuids: list[str]):
    client = RiotAPIClient(regions=settings.SUPPORTED_REGIONS)
    for puuid in puuids:
        match_ids = client.fetch_match_ids_by_puuid(puuid)
        context.log.info(f"Fetched {len(match_ids)} matches for PUUID: {puuid}")
        for match_id in match_ids:
            match_data = client.fetch_match_data(match_id)
            if match_data:
                client.process_match_data(match_data)
                context.log.info(f"Processed match ID: {match_id}")
            else:
                context.log.warning(f"No data for match ID: {match_id}")
