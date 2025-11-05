from dagster import job
from dagster_home.data_service.ops.model_training_ops import training_model_op

@job
def trigger_training_job():
    """
    Trigger the model training job to calculate and register the champion model.
    """
    training_model_op()
