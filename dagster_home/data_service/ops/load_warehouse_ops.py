from dagster import op, Out
from dagster_home.data_service.load_to_warehouse import MatchDataWarehouseLoaderS3
from loguru import logger
from settings import settings

@op(out=Out(dict), description="Process match data from S3 and load to warehouse")
def process_match_data_and_load_to_warehouse(context):
    context.log.info("Starting match data processing and loading to warehouse...")
    loader = MatchDataWarehouseLoaderS3()
    loader.run()
    table_info = {
        'schema_name': settings.WAREHOUSE_SCHEMA,
        'table_name': settings.MATCHES_TABLE
    }
    return table_info
