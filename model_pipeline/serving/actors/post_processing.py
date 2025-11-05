from model_pipeline.utils.trino_operator import TrinoDBOperator
from loguru import logger
import pandas as pd
from settings import settings

class DataLoader:
    def __init__(self, trino_connector: TrinoDBOperator):
        self.trino = trino_connector

    def load_champion_data(self):
        query = f"SELECT * FROM {settings.LAKE_SCHEMA}.{settings.CHAMPION_TABLE}"
        result = self.trino.execute_query(query)
        logger.info(f"Loaded {len(result)} match records")
        return result

class PostProcessor:
    def __init__(self, champion_recommender_results: pd.DataFrame, top_n: int, choose_positions: list[str]):
        trino_connector = TrinoDBOperator(schema=settings.LAKE_SCHEMA)
        self.data_loader = DataLoader(trino_connector=trino_connector)
        self.champion_recommender_results = champion_recommender_results
        self.top_n = top_n
        self.choose_positions = [pos.upper() for pos in choose_positions]
        logger.info(f"Initialized PostProcessor with top_n={top_n}, choose_positions={self.choose_positions}")

    def _valid_positions(self):
        valid_positions = {'TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'SUPPORT'}
        for pos in self.choose_positions:
            if pos not in valid_positions:
                logger.error(f"Invalid position: {pos}")
                raise ValueError(f"Invalid position: {pos}. Valid positions are: {valid_positions}")
        logger.info("All positions are valid.")

    def filter_by_positions(self):
        logger.info("Loading champion data...")
        champion_data = pd.DataFrame(self.data_loader.load_champion_data())
        logger.info(f"Loaded {len(champion_data)} champions from database.")

        # Preprocess positions column
        champion_data['roles'] = champion_data['roles'].str.upper().str.split(',')
        logger.debug("Processed positions column to list of roles.")

        # Merge with recommendation results
        logger.info("Merging recommendation results with champion positions...")
        merged_df = self.champion_recommender_results.merge(
            champion_data[['champion_name', 'roles']],
            left_on='champion',
            right_on='champion_name',
            how='inner'
        )
        logger.info(f"Merged data size: {len(merged_df)}")

        # Filter by selected positions
        logger.info(f"Filtering champions by positions: {self.choose_positions}")
        filtered_df = merged_df[
            merged_df['roles'].apply(lambda pos_list: any(pos in self.choose_positions for pos in pos_list))
        ]
        logger.info(f"Filtered champions count: {len(filtered_df)}")

        return filtered_df

    def get_top_n_recommendations(self, filtered_df):
        logger.info(f"Selecting top {self.top_n} recommendations...")
        top_results = filtered_df.sort_values(by='score', ascending=False).head(self.top_n)
        logger.info(f"Returning top {self.top_n} champions after filtering and sorting.")
        return top_results

    def format_results(self, top_recommendations):
        logger.info("Formatting final results...")

        formatted_results = {
            "positions": self.choose_positions,
            "num_recommendations": len(top_recommendations),
            "recommendations": []
        }

        for _, row in top_recommendations.iterrows():
            formatted_results["recommendations"].append({
                "champion_name": row["champion_name"],
                "score": row["score"],
                "positions": row["roles"]  # Already a list of roles
            })

        logger.info("Formatted results successfully.")
        return formatted_results

    def run(self):
        self._valid_positions()
        filtered_df = self.filter_by_positions()
        top_recommendations = self.get_top_n_recommendations(filtered_df)
        return self.format_results(top_recommendations)
