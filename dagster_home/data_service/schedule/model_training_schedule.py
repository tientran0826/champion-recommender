from dagster_home.data_service.jobs.training_job import trigger_training_job
from dagster import schedule
from dagster_home.data_service.configs import configs
from datetime import datetime, timedelta
@schedule(
    job=trigger_training_job,
    cron_schedule=configs.MODEL_TRAINING_RUNTIME,  # Using runtime from configs.py
    execution_timezone="Asia/Bangkok"  # Valid IANA timezone for UTC+7
)
def monthly_model_training_schedule(context):
    return {
        "ops": {
            "training_model_op": {
                "config": {
                    "training_start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                    "training_end_date": datetime.now().strftime("%Y-%m-%d"),
                    "experiment_name": "champion_recommender",
                    "register_as_production": True
                }
            },
        }
    }
