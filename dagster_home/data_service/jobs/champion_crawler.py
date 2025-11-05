from dagster_home.data_service.ops.api_ops import fetch_champion_roles
from dagster_home.data_service.ops.sync_table_trino import sync_trino_partitions
from dagster import job

@job
def champion_crawler_job():
    """
    API crawler job to fetch and process champion data.
    """
    champion_table_info = fetch_champion_roles()
    sync_trino_partitions(champion_table_info)
