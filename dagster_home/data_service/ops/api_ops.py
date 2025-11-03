from dagster import op
from dagster_home.data_service.crawler_job import RiotAPIClient
from settings import settings
from loguru import logger

@op
def fetch_challenger_data(context):
    client = RiotAPIClient(regions=settings.SUPPORTED_REGIONS)
    data = client.fetch_challenger_data()
    processed_data = client.process_challenger_data(data)

    # Use Dagster's context logger
    context.log.info(f"Processed {len(processed_data)} players")

    return processed_data
