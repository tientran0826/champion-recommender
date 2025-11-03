from dagster import sensor, RunRequest, SkipReason, DagsterRunStatus, DefaultSensorStatus, RunsFilter
from loguru import logger

@sensor(
    job_name="load_data_to_warehouse",
    default_status=DefaultSensorStatus.RUNNING,
    minimum_interval_seconds=60
)
def trigger_warehouse_after_api_crawler(context):
    """Trigger warehouse load after API crawler succeeds"""

    # Use RunsFilter object instead of dict
    runs = context.instance.get_runs(
        filters=RunsFilter(
            job_name="api_crawler_job",
            statuses=[DagsterRunStatus.SUCCESS]
        ),
        limit=1
    )

    if not runs:
        return SkipReason("No successful api_crawler_job runs found")

    latest_run = runs[0]
    cursor = context.cursor or "0"

    if latest_run.run_id <= cursor:
        return SkipReason(f"Already processed run {latest_run.run_id}")

    logger.info(f"Triggering warehouse load after api_crawler run: {latest_run.run_id}")
    context.log.info(f"API crawler run {latest_run.run_id} completed successfully, triggering warehouse load")

    context.update_cursor(latest_run.run_id)

    return RunRequest(
        run_key=f"warehouse_after_{latest_run.run_id}",
        tags={
            "triggered_by": "api_crawler_job",
            "source_run_id": latest_run.run_id,
            "api_crawler_status": latest_run.status.value
        }
    )
