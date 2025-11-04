from datetime import datetime
import pandas as pd
from dagster_home.data_service.utils.db_operator import S3Operator
from loguru import logger
from settings import settings
from io import StringIO

class MatchDataWarehouseLoaderS3:
    """
    Load Riot match data from S3Operator, transform, and save transformed data back to S3 as CSV.
    """

    def __init__(self):
        # Debug: Show what bucket we're using
        logger.info(f"Initializing with bucket: {settings.S3_DATA_BUCKET}")

        self.s3_operator = S3Operator(
            endpoint=settings.S3_ENDPOINT,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            bucket_name=settings.S3_DATA_BUCKET
        )
        self.warehouse_prefix = "curated/matches/"

    def list_match_files(self):
        """List all JSON files from S3 bucket under 'raw/matches/' prefix"""
        try:
            # The prefix should be just 'raw/matches/' because bucket is already set
            logger.info(f"Listing objects with prefix: raw/matches/")

            keys = self.s3_operator.list_objects(prefix="raw/matches/", recursive=True)

            logger.info(f"Total keys found: {len(keys)}")
            if keys:
                logger.info(f"Sample keys: {keys[:3]}")

            json_keys = [k for k in keys if k.endswith(".json")]
            logger.info(f"Found {len(json_keys)} JSON files in raw/matches/")

            return json_keys
        except Exception as e:
            logger.error(f"Failed to list match files: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def read_match_json(self, key: str) -> dict:
        """Read a single match JSON from S3"""
        try:
            data = self.s3_operator.download_json(key)
            if not data:
                logger.warning(f"Empty data for {key}")
                return None
            logger.debug(f"Successfully read {key}")
            return data
        except Exception as e:
            logger.error(f"Failed to read {key}: {e}")
            return None

    def transform_match(self, match_data: dict) -> pd.DataFrame:
        """Transform raw match JSON into DataFrame with timestamp - RANKED SOLO 5v5 ONLY"""
        if not match_data:
            return pd.DataFrame()

        try:
            # Check if this is a ranked solo queue match
            queue_id = match_data['info'].get('queueId')
            game_mode = match_data['info'].get('gameMode', '')
            game_type = match_data['info'].get('gameType', '')

            # Ranked Solo/Duo queue ID is 420
            if queue_id != 420:
                logger.debug(f"Skipping match {match_data['metadata']['matchId']} - not solo queue (queueId: {queue_id})")
                return pd.DataFrame()

            # Additional validation
            if game_mode != 'CLASSIC' or game_type != 'MATCHED_GAME':
                logger.debug(f"Skipping match - invalid game mode/type: {game_mode}/{game_type}")
                return pd.DataFrame()

            # Verify it's 5v5 (10 participants)
            participants = match_data['info']['participants']
            if len(participants) != 10:
                logger.debug(f"Skipping match - not 5v5 ({len(participants)} participants)")
                return pd.DataFrame()

            team1 = []
            team2 = []
            for p in participants:
                if p['teamId'] == 100:
                    team1.append(p['championName'])
                else:
                    team2.append(p['championName'])

            # Verify teams are 5v5
            if len(team1) != 5 or len(team2) != 5:
                logger.debug(f"Skipping match - invalid team sizes: {len(team1)}v{len(team2)}")
                return pd.DataFrame()

            team1_win = any(p.get('win', False) for p in participants if p['teamId'] == 100)

            ts_ms = match_data['info']['gameStartTimestamp']
            game_start = datetime.fromtimestamp(ts_ms / 1000)
            game_start_str = game_start.strftime("%Y-%m-%d %H:%M:%S.%f")

            df = pd.DataFrame([{
                "match_id": match_data['metadata']['matchId'],
                "team1_champions": ",".join(team1),
                "team2_champions": ",".join(team2),
                "team1_win": team1_win,
                "game_start": game_start_str
            }])

            logger.debug(f"✅ Transformed RANKED SOLO match {match_data['metadata']['matchId']}")
            return df

        except Exception as e:
            logger.error(f"Failed to transform match: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()

    def run(self):
        """Full pipeline: list → read → transform → concat → deduplicate → save partitioned by date"""
        logger.info("Starting warehouse load process...")

        files = self.list_match_files()
        if not files:
            logger.warning("No match files found in S3. Exiting.")
            return

        logger.info(f"Processing {len(files)} match files...")

        all_dfs = []
        for idx, key in enumerate(files, 1):
            logger.info(f"Processing file {idx}/{len(files)}: {key}")
            match_json = self.read_match_json(key)
            if not match_json:
                continue

            df = self.transform_match(match_json)
            if not df.empty:
                all_dfs.append(df)

        if not all_dfs:
            logger.warning("No valid match data found after transformation. Exiting.")
            return

        logger.info(f"Successfully transformed {len(all_dfs)} matches")

        final_df = pd.concat(all_dfs, ignore_index=True)
        logger.info(f"Total records before dedup: {len(final_df)}")

        final_df = final_df.drop_duplicates(subset="match_id")
        logger.info(f"Total records after dedup: {len(final_df)}")

        final_df["game_start"] = pd.to_datetime(final_df["game_start"])
        final_df = final_df.sort_values("game_start")
        final_df["game_date"] = final_df["game_start"].dt.strftime("%Y-%m-%d")

        for game_date, df_partition in final_df.groupby("game_date"):
            logger.info(f"Saving partition for date {game_date} ({len(df_partition)} records)...")

            try:
                csv_buffer = StringIO()
                df_partition.to_csv(csv_buffer, index=False)
                csv_content = csv_buffer.getvalue()

                key = f"{self.warehouse_prefix}date={game_date}/matches.csv"
                logger.info(f"Uploading to {key} (size: {len(csv_content)} bytes)")

                success = self.s3_operator.upload_fileobj(
                    key=key,
                    fileobj=csv_content.encode('utf-8')
                )

                if success:
                    logger.info(f"Saved {len(df_partition)} matches for {game_date} to S3: {key}")
                else:
                    logger.error(f"Failed to save matches for {game_date} to S3: {key}")

            except Exception as e:
                logger.error(f"Exception saving partition {game_date}: {e}")
                import traceback
                logger.error(traceback.format_exc())

        logger.info("Warehouse load process completed!")
