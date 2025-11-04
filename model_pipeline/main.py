from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from model_pipeline.training.pipeline import TrainingPipeline
import mlflow
import mlflow.pyfunc
from loguru import logger
from settings import settings
import numpy as np
import uuid
import os
import sys
from typing import List, Optional
from mlflow.tracking import MlflowClient

os.environ["MLFLOW_DEFAULT_ARTIFACT_ROOT"] = f"s3://{settings.S3_DATA_BUCKET}/mlflow/artifacts"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = settings.MLFLOW_S3_ENDPOINT_URL
os.environ["AWS_ACCESS_KEY_ID"] = settings.S3_ACCESS_KEY
os.environ["AWS_SECRET_ACCESS_KEY"] = settings.S3_SECRET_KEY

mlflow.set_tracking_uri(settings.MLFLOW_BACKEND_STORE_URI)

app = FastAPI()
training_jobs = {}

class TrainingRequest(BaseModel):
    training_start_date: Optional[str] = None
    training_end_date: Optional[str] = None
    experiment_name: Optional[str] = "champion_recommender"
    register_as_production: bool = True

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
    model_version: Optional[int] = None
    error: Optional[str] = None
    metrics: Optional[dict] = None
class ChampionRecommenderModel(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        import json
        with open(context.artifacts["champion_relations"], "r") as f:
            self.relations = json.load(f)

    def predict(self, context, model_input):
        champion_name = model_input.get("champion_name")
        if champion_name in self.relations["champion_index"]:
            return self.relations["champion_index"][champion_name]
        return None

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
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


def run_training_pipeline(
    job_id: str,
    training_start_date: str,
    training_end_date: str,
    experiment_name: str,
    register_as_production: bool = True
):
    logger.info(f"Starting job {job_id}")

    try:
        training_jobs[job_id]["status"] = "running"
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name=f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}") as run:
            run_id = run.info.run_id

            mlflow.log_param("training_start_date", training_start_date)
            mlflow.log_param("training_end_date", training_end_date)
            mlflow.log_param("job_id", job_id)

            pipeline = TrainingPipeline(training_start_date=training_start_date, training_end_date=training_end_date)

            raw_data = pipeline.fetch_match_data()
            total_matches = len(raw_data)
            mlflow.log_metric("total_matches", total_matches)

            processed_data = pipeline.preprocess_data(raw_data)
            num_champions = len(processed_data["champion_index"])
            mlflow.log_metric("num_champions", num_champions)

            import tempfile
            import json

            serializable_data = pipeline._convert_numpy_to_serializable(processed_data)

            with tempfile.TemporaryDirectory() as tmpdir:
                relations_path = os.path.join(tmpdir, "champion_relations.json")
                with open(relations_path, "w") as f:
                    json.dump(serializable_data, f, indent=2)

                # Save the MLflow model
                model_artifact_path = "model"
                mlflow.pyfunc.log_model(
                    artifact_path=model_artifact_path,   # logged under run'
                    python_model=ChampionRecommenderModel(),
                    artifacts={"champion_relations": relations_path}
                )
            # Save also to S3 (your original logic)
            s3_key = f"model_artifacts/{training_start_date}/champion_relations.json"
            pipeline.save_result_to_s3(processed_data, key=s3_key)
            mlflow.log_param("s3_artifact_location", f"s3://{settings.S3_DATA_BUCKET}/{s3_key}")

            model_version = None
            model_name = "champion_recommender"

            if register_as_production:
                try:

                    client = MlflowClient()

                    # Ensure model registry exists
                    try:
                        client.get_registered_model(model_name)
                    except:
                        client.create_registered_model(name=model_name)

                    # Register model
                    model_uri = f"runs:/{run_id}/{model_artifact_path}"
                    model_details = mlflow.register_model(model_uri=model_uri, name=model_name)
                    model_version = model_details.version

                    # Set alias to production
                    client.set_registered_model_alias(
                        name=model_name,
                        alias="production",
                        version=model_version
                    )

                    client.update_model_version(
                        name=model_name,
                        version=model_version,
                        description=f"Run {run_id}, matches {total_matches}"
                    )

                except Exception as e:
                    logger.error(f"Model registration failed: {e}")

            training_jobs[job_id].update({
                "status": "completed",
                "mlflow_run_id": run_id,
                "model_version": model_version,
                "metrics": {
                    "total_matches": total_matches,
                    "num_champions": num_champions
                }
            })

            logger.info(f"Job {job_id} completed. Run ID: {run_id}, Model version: {model_version}")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        training_jobs[job_id].update({
            "status": "failed",
            "error": str(e)
        })

@app.post("/train-model", response_model=TrainingResponse)
async def trigger_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    if request.training_start_date is None:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        start_date = request.training_start_date

    end_date = request.training_end_date or datetime.now().strftime("%Y-%m-%d")
    job_id = str(uuid.uuid4())

    training_jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "training_start_date": start_date,
        "training_end_date": end_date,
        "experiment_name": request.experiment_name
    }

    background_tasks.add_task(
        run_training_pipeline,
        job_id=job_id,
        training_start_date=start_date,
        training_end_date=end_date,
        experiment_name=request.experiment_name,
        register_as_production=request.register_as_production
    )

    return TrainingResponse(
        job_id=job_id,
        status="queued",
        message="Training job queued",
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

@app.get("/models/production")
async def get_production_model():
    """Get current production model info including artifact S3 path"""
    try:
        client = MlflowClient()
        model_name = "champion_recommender"

        alias_used = True
        try:
            # Try to get the production model by alias
            model_version = client.get_model_version_by_alias(model_name, "production")
        except Exception as alias_error:
            alias_used = False
            logger.warning(f"No production alias found: {alias_error}")
            # fallback to latest version
            versions = client.search_model_versions(f"name='{model_name}'")
            if not versions:
                return {"message": "No model versions found", "hint": "Try training a model first"}
            model_version = max(versions, key=lambda v: int(v.version))

        # Get the run info to fetch parameters
        run_id = model_version.run_id
        run_data = mlflow.get_run(run_id).data

        # Extract the S3 artifact location if logged
        s3_path = run_data.params.get("s3_artifact_location", None)

        return {
            "model_name": model_name,
            "version": model_version.version,
            "alias": "production" if alias_used else "none",
            "run_id": run_id,
            "source": model_version.source,
            "tags": model_version.tags,
            "description": model_version.description,
            "creation_timestamp": model_version.creation_timestamp,
            "s3_artifact_location": s3_path
        }

    except Exception as e:
        logger.error(f"Error getting production model: {e}")
        raise HTTPException(status_code=500, detail=str(e))
