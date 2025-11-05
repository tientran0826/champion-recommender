from dagster_home.data_service.jobs.champion_crawler import champion_crawler_job
from dagster import schedule
from dagster_home.data_service.configs import configs
@schedule(
    job=champion_crawler_job,
    cron_schedule=configs.INGEST_DATA_RUNTIME,  # Using runtime from configs.py
    execution_timezone="Asia/Bangkok"  # Valid IANA timezone for UTC+7
)
def daily_champion_crawler_schedule(context):
    return {

    }
