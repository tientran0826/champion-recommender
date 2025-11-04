from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from model_pipeline.training.pipeline import TrainingPipeline
import mlflow
from loguru import logger
from settings import settings
import numpy as np
import uuid
import os

os.environ["MLFLOW_DEFAULT_ARTIFACT_ROOT"] = f"s3://{settings.S3_DATA_BUCKET}/mlflow/artifacts"

# Configure MLflow BEFORE creating the app
os.environ["MLFLOW_S3_ENDPOINT_URL"] = settings.MLFLOW_S3_ENDPOINT_URL
os.environ["AWS_ACCESS_KEY_ID"] = settings.S3_ACCESS_KEY
os.environ["AWS_SECRET_ACCESS_KEY"] = settings.S3_SECRET_KEY

# Set MLflow tracking URI to your server
mlflow.set_tracking_uri(settings.MLFLOW_BACKEND_STORE_URI)

app = FastAPI()

training_jobs = {}

class TrainingRequest(BaseModel):
    training_start_date: Optional[str] = None
    training_end_date: Optional[str] = None
    experiment_name: Optional[str] = "champion_recommender"

class TrainingResponse(BaseModel):
    job_id: str
    status: str
    message: str
    training_start_date: str
    training_end_date: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    training_start_date: Optional[str] = None
    training_end_date: Optional[str] = None
    mlflow_run_id: Optional[str] = None
    error: Optional[str] = None
    metrics: Optional[dict] = None

def run_training_pipeline(
    job_id: str,
    training_start_date: str,
    training_end_date: str,
    experiment_name: str
):
    """Background task to run training pipeline"""
    try:
        training_jobs[job_id]["status"] = "running"

        # Setup MLflow
        mlflow.set_experiment(experiment_name)

        # Start MLflow run
        with mlflow.start_run(run_name=f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            # Log parameters
            mlflow.log_param("training_start_date", training_start_date)
            mlflow.log_param("training_end_date", training_end_date)
            mlflow.log_param("job_id", job_id)

            # Run training
            pipeline = TrainingPipeline(
                training_start_date=training_start_date,
                training_end_date=training_end_date
            )

            logger.info(f"Job {job_id}: Fetching data...")
            raw_data = pipeline.fetch_match_data()
            mlflow.log_metric("total_matches", len(raw_data))
            logger.info(f"Job {job_id}: Fetched {len(raw_data)} matches")
            logger.info(f"Job {job_id}: Processing data...")
            processed_data = pipeline.preprocess_data(raw_data)

            # Log metrics
            num_champions = len(processed_data['champion_index'])
            mlflow.log_metric("num_champions", num_champions)

            # Log artifacts
            import tempfile
            import os
            import json

            with tempfile.TemporaryDirectory() as tmpdir:
                # Save parameters
                params_path = os.path.join(tmpdir, "parameters.json")
                with open(params_path, 'w') as f:
                    json.dump({
                        "num_champions": num_champions,
                        "total_matches": len(raw_data)
                    }, f, indent=2)
                mlflow.log_artifact(params_path)
                logger.info(f"Logged parameters to MLflow")

                # ALSO save the combined champion_relations.json to MLflow
                combined_path = os.path.join(tmpdir, "champion_relations.json")
                serializable_data = pipeline._convert_numpy_to_serializable(processed_data)
                with open(combined_path, 'w') as f:
                    json.dump(serializable_data, f, indent=2)
                mlflow.log_artifact(combined_path)
                logger.info(f"Logged champion_relations.json to MLflow")

            # Save to S3
            key = f"model_artifacts/{training_start_date}/champion_relations.json"
            pipeline.save_result_to_s3(processed_data, key=key)
            mlflow.log_param("s3_artifact_location", f"s3://{settings.S3_DATA_BUCKET}/{key}")

            # Update job status
            training_jobs[job_id].update({
                "status": "completed",
                "mlflow_run_id": mlflow.active_run().info.run_id,
                "metrics": {
                    "total_matches": len(raw_data),
                    "num_champions": num_champions,
                }
            })

            logger.info(f"✅ Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        training_jobs[job_id].update({
            "status": "failed",
            "error": str(e)
        })

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test MLflow connection
        mlflow.search_experiments(max_results=1)
        mlflow_status = "connected"
    except Exception as e:
        mlflow_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "service": "training-api",
        "mlflow_uri": mlflow.get_tracking_uri(),
        "mlflow_status": mlflow_status
    }

@app.post("/train-model", response_model=TrainingResponse)
async def trigger_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
):
    """Trigger model training"""

    # Set default dates if not provided
    if request.training_start_date is None:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        start_date = request.training_start_date

    end_date = request.training_end_date or datetime.now().strftime("%Y-%m-%d")
    # Generate job ID
    job_id = str(uuid.uuid4())

    # Store job info
    training_jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "training_start_date": start_date,
        "training_end_date": end_date,
        "experiment_name": request.experiment_name
    }

    # Start background training
    background_tasks.add_task(
        run_training_pipeline,
        job_id=job_id,
        training_start_date=start_date,
        training_end_date=end_date,
        experiment_name=request.experiment_name
    )

    logger.info(f"Training job {job_id} queued")

    return TrainingResponse(
        job_id=job_id,
        status="queued",
        message="Training job has been queued",
        training_start_date=start_date,
        training_end_date=end_date
    )

@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get status of a training job"""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(**training_jobs[job_id])

@app.get("/jobs")
async def list_jobs():
    """List all training jobs"""
    return {"jobs": list(training_jobs.values())}
