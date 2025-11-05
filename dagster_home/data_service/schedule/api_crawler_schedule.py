from dagster_home.data_service.jobs.api_crawler import api_crawler_job
from dagster import schedule
from dagster_home.data_service.configs import configs
@schedule(
    job=api_crawler_job,
    cron_schedule=configs.INGEST_DATA_RUNTIME,  # Using runtime from configs.py
    execution_timezone="Asia/Bangkok"  # Valid IANA timezone for UTC+7
)
def daily_api_crawler_schedule(context):

    return {
        "ops": {
            "fetch_challenger_data": {
                "config": {
                    "supported_regions": ["kr"]
                }
            },
            "fetch_match_data_by_puuids": {
                "config": {
                    "max_matches_per_puuid": 20,
                    "test_mode": False
                }
            }
        }
    }
