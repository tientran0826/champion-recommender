from dagster import repository
from dagster_home.data_service.jobs.api_crawler import api_crawler_job
from dagster_home.data_service.jobs.load_data_to_warehouse import load_data_to_warehouse
from dagster_home.data_service.sensors import trigger_warehouse_after_api_crawler
from dagster_home.data_service.schedule import daily_api_crawler_schedule
@repository
def data_service_repository():
    """Repository containing all jobs and sensors"""
    return [
        # Jobs
        api_crawler_job,
        load_data_to_warehouse,
        # Schedules
        daily_api_crawler_schedule,
        # Sensors
        trigger_warehouse_after_api_crawler,
    ]
