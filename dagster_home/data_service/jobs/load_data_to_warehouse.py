from dagster_home.data_service.ops.load_warehouse_ops import process_match_data_and_load_to_warehouse
from dagster import job

@job
def load_data_to_warehouse():
    process_match_data_and_load_to_warehouse()
