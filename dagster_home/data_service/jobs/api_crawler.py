from dagster_home.data_service.ops.api_ops import fetch_challenger_data
from dagster import job

@job
def api_crawler_job():
    fetch_challenger_data()
