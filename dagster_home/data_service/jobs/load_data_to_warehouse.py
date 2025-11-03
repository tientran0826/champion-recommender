from dagster_home.data_service.ops.load_warehouse_ops import process_match_data_and_load_to_warehouse
from dagster_home.data_service.ops.sync_table_trino import sync_trino_partitions
from dagster import job

@job
def load_data_to_warehouse():
    """
    Complete warehouse pipeline:
    1. Process match data from raw S3 → curated CSV
    2. Sync Trino partitions to discover new data
    """
    table_info = process_match_data_and_load_to_warehouse()
    sync_trino_partitions(table_info)
