from dagster import repository
from dagster_home.data_service.jobs.match_crawler import  match_crawler_job
from dagster_home.data_service.jobs.load_data_to_warehouse import load_data_to_warehouse
from dagster_home.data_service.jobs.champion_crawler import champion_crawler_job
from dagster_home.data_service.jobs.training_job import trigger_training_job
from dagster_home.data_service.sensors import trigger_warehouse_after_api_crawler
from dagster_home.data_service.schedule import daily_match_crawler_schedule, monthly_model_training_schedule, daily_champion_crawler_schedule

@repository
def data_service_repository():
    """Repository containing all jobs and sensors"""
    return [
        # Jobs
        match_crawler_job,
        load_data_to_warehouse,
        trigger_training_job,
        champion_crawler_job,
        # Schedules
        daily_match_crawler_schedule,
        monthly_model_training_schedule,
        daily_champion_crawler_schedule,
        # Sensors
        trigger_warehouse_after_api_crawler,
    ]
