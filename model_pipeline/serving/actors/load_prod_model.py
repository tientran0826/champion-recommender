
from mlflow.tracking import MlflowClient
from loguru import logger
from fastapi import HTTPException

class ModelLoader:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.client = MlflowClient()

    def get_production_model(self):
        """Get current production model info including artifact S3 path"""
        try:
            alias_used = True
            try:
                # Try to get the production model by alias
                model_version = self.client.get_model_version_by_alias(self.model_name, "production")
            except Exception as alias_error:
                alias_used = False
                logger.warning(f"No production alias found: {alias_error}")
                # fallback to latest version
                versions = self.client.search_model_versions(f"name='{self.model_name}'")
                if not versions:
                    return {"message": "No model versions found", "hint": "Try training a model first"}
                model_version = max(versions, key=lambda v: int(v.version))

            # Get the run info to fetch parameters
            run_id = model_version.run_id
            run_data = self.client.get_run(run_id).data

            # Extract the S3 artifact location if logged
            s3_path = run_data.params.get("s3_artifact_location", None)

            return {
                "model_name": self.model_name,
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
