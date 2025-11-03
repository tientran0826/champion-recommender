from dagster_home.data_service.ops.api_ops import fetch_challenger_data, fetch_match_data_by_puuids
from dagster_home.data_service.ops.sync_table_trino import sync_trino_partitions
from dagster import job

@job
def api_crawler_job():
    """
    API crawler job to fetch and process match data.
    """
    puuids = fetch_challenger_data()
    table_info = fetch_match_data_by_puuids(puuids)
    sync_trino_partitions(table_info)
