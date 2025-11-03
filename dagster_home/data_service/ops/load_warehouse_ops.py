import time
from dagster import op
from dagster_home.data_service.load_to_warehouse import MatchDataWarehouseLoaderS3
from loguru import logger

@op
def process_match_data_and_load_to_warehouse(context):
    context.log.info("Starting match data processing and loading to warehouse...")
    loader = MatchDataWarehouseLoaderS3()
    loader.run()
