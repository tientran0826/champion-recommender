
from data_service.utils.common import request_riot_api
from data_service.configs import configs

class RiotAPIClient:
    def __init__(self, regions: list[str]):
        self.regions = regions

    def fetch_challenger_data(self):
        results = {}
        for region in self.regions:
            response = request_riot_api(region=region, endpoint=f"{configs.CHALLENGER_ENDPOINT}/{configs.SOLO_QUEUE}")
            results[region] = response
        return results

print(RiotAPIClient(regions=["NA1", "EUW1"]).fetch_challenger_data())
