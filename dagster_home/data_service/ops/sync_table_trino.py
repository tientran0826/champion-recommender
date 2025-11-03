from dagster import op, In
from loguru import logger
from settings import settings
import trino

@op(ins={"table_info": In(dict)}, description="Sync Trino table partitions to discover new data")
def sync_trino_partitions(context, table_info: dict) -> bool:
    """
    Sync Trino table partitions to discover new data.
    Executes: CALL system.sync_partition_metadata('warehouse', 'matches', 'ADD')
    """
    schema_name = table_info.get('schema_name')
    table_name = table_info.get('table_name')
    if not schema_name or not table_name:
        context.log.warning("Schema name or table name not provided. Skipping partition sync.")
        return False
    try:
        # Connect to Trino
        conn = trino.dbapi.connect(
            host=settings.TRINO_HOST,
            port=settings.TRINO_PORT,
            user=settings.TRINO_USER,
            catalog=settings.TRINO_CATALOG,
            schema=schema_name
        )

        cursor = conn.cursor()

        # Sync partitions
        sync_sql = f"CALL system.sync_partition_metadata('{schema_name}', '{table_name}', 'ADD')"
        context.log.info(f"Executing: {sync_sql}")
        cursor.execute(sync_sql)

        # Verify partitions
        cursor.execute(f"SHOW PARTITIONS {schema_name}.{table_name}")
        partitions = cursor.fetchall()
        context.log.info(f"Found {len(partitions)} partitions after sync")

        for partition in partitions:
            context.log.debug(f"  Partition: {partition}")

        # Get row count
        cursor.execute("SELECT COUNT(*) FROM hive.warehouse.matches")
        count = cursor.fetchone()[0]
        context.log.info(f"Total rows in matches table: {count}")

        cursor.close()
        conn.close()

        logger.info(f"✅ Successfully synced {len(partitions)} partitions with {count} total rows")
        return True

    except Exception as e:
        context.log.error(f"❌ Failed to sync partitions: {e}")
        logger.error(f"Partition sync failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
