from model_pipeline.serving.actors.load_prod_model import ModelLoader
from model_pipeline.serving.actors.post_processing import PostProcessor
from model_pipeline.serving.actors.recommender import ChampionRecommender
from model_pipeline.utils.s3_operator import S3Operator
from settings import settings

class ServingPipeline:
    def __init__(self, model_name: str, allies: list[str], opponents: list[str], choose_positions: list[str], bans: list[str] = None):
        self.model_name = model_name
        self.allies = allies
        self.opponents = opponents
        self.bans = bans if bans is not None else []
        self.choose_positions = choose_positions
        self.s3_operator = S3Operator(bucket_name=settings.S3_DATA_BUCKET,
                                 endpoint=settings.S3_ENDPOINT,
                                 access_key=settings.S3_ACCESS_KEY,
                                 secret_key=settings.S3_SECRET_KEY,
                                 secure=False)

    def load_production_model(self):
        model_loader = ModelLoader(model_name=self.model_name)
        return model_loader.get_production_model()

    def predict(self, top_n: int = 5):
        champion_relations = self.load_production_model().get('s3_artifact_location')
        champion_relations = champion_relations.replace("s3://", "")
        _, key = champion_relations.split("/", 1)
        relations_dict = self.s3_operator.download_json(key=key)
        if relations_dict is None:
            raise ValueError(f"Failed to load relations from S3 path: {champion_relations}")
        recommender = ChampionRecommender(relations=relations_dict)
        raw_result = recommender.recommend_weighted(
            allies=self.allies,
            opponents=self.opponents,
            bans=self.bans,
        )
        post_processor = PostProcessor(
            champion_recommender_results=raw_result,
            top_n=top_n,
            choose_positions=self.choose_positions
        )

        response = post_processor.run()
        return response
