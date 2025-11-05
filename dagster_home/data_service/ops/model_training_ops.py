from dagster import op, Config
from typing import Optional
import requests
from settings import settings


class TrainingOpConfig(Config):
    """Config for training model operation"""
    training_start_date: Optional[str] = None
    training_end_date: Optional[str] = None
    experiment_name: str = "champion_recommender"
    register_as_production: bool = True

@op
def training_model_op(context, config: TrainingOpConfig):
    """Trigger model training via FastAPI"""

    fastapi_url = f"{settings.FASTAPI_HOST}/train-model"

    # Prepare payload
    payload = {
        "training_start_date": config.training_start_date,
        "training_end_date": config.training_end_date,
        "experiment_name": config.experiment_name,
        "register_as_production": config.register_as_production
    }

    context.log.info(f"Triggering training with payload: {payload}")
    context.log.info(f"FastAPI URL: {fastapi_url}")

    try:
        response = requests.post(
            fastapi_url,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            context.log.info(f"Success: Model training triggered")
            context.log.info(f"Job ID: {result.get('job_id')}")
            context.log.info(f"Status: {result.get('status')}")
            context.log.info(f"Dates: {result.get('training_start_date')} to {result.get('training_end_date')}")
            return result
        else:
            context.log.error(f"Failed: {response.text}")
            response.raise_for_status()

    except requests.exceptions.RequestException as e:
        context.log.error(f"Request failed: {str(e)}")
        raise
