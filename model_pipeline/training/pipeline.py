

from model_pipeline.training.actors.load_data import DataLoader
from model_pipeline.utils.trino_operator import TrinoDBOperator
from model_pipeline.utils.s3_operator import S3Operator
from model_pipeline.training.actors.matrix_calculator import ChampionRelations
from settings import settings
from datetime import datetime
import numpy as np
import mlflow

class TrainingPipeline:
    def __init__(self, training_start_date: str, training_end_date: str=None):
        self.data_loader = self.connect_data_loader()
        self.training_start_date = training_start_date
        self.training_end_date = datetime.now().strftime("%Y-%m-%d") if training_end_date is None else training_end_date

    def connect_data_loader(self) -> DataLoader:
        trino_operator = TrinoDBOperator(schema=settings.WAREHOUSE_SCHEMA)
        data_loader = DataLoader(trino_connector=trino_operator)
        return data_loader

    def fetch_match_data(self):
        return self.data_loader.load_match_data(self.training_start_date, self.training_end_date)

    def preprocess_data(self, raw_data):
        # Implement preprocessing logic here
        champion_relations = ChampionRelations(raw_data)
        synergy_matrix, counter_matrix = champion_relations.calculate()
        champion_index = champion_relations.get_champ_index()
        ts, tc = champion_relations.get_ts_tc()

        result = {
            "Ts": ts,
            "Tc": tc,
            "synergy_matrix": synergy_matrix,
            "counter_matrix": counter_matrix,
            "champion_index": champion_index
        }
        return result

    def save_result_to_s3(self, result, key):
        s3_operator = S3Operator(bucket_name=settings.S3_DATA_BUCKET,
                                 endpoint=settings.S3_ENDPOINT,
                                 access_key=settings.S3_ACCESS_KEY,
                                 secret_key=settings.S3_SECRET_KEY,
                                 secure=False)
        serializable_result = self._convert_numpy_to_serializable(result)
        s3_operator.upload_json(data=serializable_result, key=key)

    def _convert_numpy_to_serializable(self, obj):
        """Convert numpy arrays to lists for JSON serialization"""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_to_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_to_serializable(item) for item in obj]
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        return obj

    def split_data(self, data, validation_ratio=0.2):
        # Implement data splitting logic here
        split_index = int(len(data) * (1 - validation_ratio))
        training_data = data[:split_index]
        validation_data = data[split_index:]
        return training_data, validation_data

    def run(self):
        raw_data = self.fetch_match_data()
        processed_data = self.preprocess_data(raw_data)

        key = f"model_artifacts/{self.training_start_date}/champion_relations.json"
        self.save_result_to_s3(processed_data, key=key)
        return processed_data
