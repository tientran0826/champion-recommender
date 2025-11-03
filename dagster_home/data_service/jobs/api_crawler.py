from dagster_home.data_service.ops.api_ops import fetch_challenger_data, fetch_match_data_by_puuids
from dagster import job

@job
def api_crawler_job():
    puuids = fetch_challenger_data()
    fetch_match_data_by_puuids(puuids)
