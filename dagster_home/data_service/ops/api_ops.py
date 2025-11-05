import time
from dagster import op, Out, Field
from dagster_home.data_service.crawler_job import RiotAPIClient
from settings import settings
from loguru import logger

@op(
    config_schema={
        "supported_regions": Field(
            [str],
            is_required=False,
            default_value=settings.SUPPORTED_REGIONS,
            description="List of regions to fetch data from"
        )
    },
    description="Fetch challenger data from Riot API and process PUUIDs"
)
def fetch_challenger_data(context):
    regions = context.op_config.get("supported_regions", settings.SUPPORTED_REGIONS)

    client = RiotAPIClient(regions=regions)
    data = client.fetch_challenger_data()
    processed_puuids = client.process_challenger_data(data)

    context.log.info(f"Processed {len(processed_puuids)} players from regions: {regions}")

    return processed_puuids

@op(
    config_schema={
        "max_matches_per_puuid": Field(
            int,
            is_required=False,
            default_value=10,
            description="Maximum number of matches to fetch per player"
        ),
        "test_mode": Field(
            bool,
            is_required=False,
            default_value=False,
            description="If true, run in test mode with limited data"
        )
    },
    out=Out(dict),
    description="Fetch match data by PUUIDs and process them"
)
def fetch_match_data_by_puuids(context, puuids: list[str]):
    max_matches = context.op_config.get("max_matches_per_puuid", 10)
    test_mode = context.op_config.get("test_mode", False)
    if test_mode:
        puuids = puuids[:5]
        context.log.info("Running in test mode: limiting to first 5 PUUIDs")
    client = RiotAPIClient(regions=settings.SUPPORTED_REGIONS)

    for puuid in puuids:
        match_ids = client.fetch_match_ids_by_puuid(puuid)
        context.log.info(f"Fetched {max_matches} matches for PUUID: {puuid}")

        for idx, match_id in enumerate(match_ids):
            if idx >= max_matches:
                break
            match_data = client.fetch_match_data(match_id)
            if match_data:
                client.process_match_data(match_data)
                context.log.info(f"Processed match ID: {match_id}")
            else:
                context.log.warning(f"No data for match ID: {match_id}")

    table_info = {
        'schema_name': settings.LAKE_SCHEMA,
        'table_name': settings.PLAYERS_TABLE
    }
    return table_info


@op(
    out=Out(dict),
    description="Fetch champion roles and images from Riot API"
)
def fetch_champion_roles(context):
    client = RiotAPIClient(regions=settings.SUPPORTED_REGIONS)
    client.fetch_champion_roles()
    table_info = {
        'schema_name': settings.LAKE_SCHEMA,
        'table_name': settings.CHAMPION_TABLE
    }
    return table_info
