from model_pipeline.utils.trino_operator import TrinoDBOperator
from settings import settings
import trino
from loguru import logger

class DataLoader:
    def __init__(self, trino_connector: TrinoDBOperator):
        self.trino = trino_connector

    def load_match_data(self, from_date: str = None, to_date: str = None):
        logger.info(f"Loading match data from {from_date} to {to_date}")
        query = f"SELECT * FROM {settings.WAREHOUSE_SCHEMA}.{settings.MATCHES_TABLE}"
        if from_date and to_date:
            query += f" WHERE game_date BETWEEN '{from_date}' AND '{to_date}'"
        result = self.trino.execute_query(query)
        logger.info(f"Loaded {len(result)} match records")
        return result
