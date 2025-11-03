CREATE SCHEMA IF NOT EXISTS hive.lake;

DROP TABLE IF EXISTS hive.lake.players;

CREATE TABLE IF NOT EXISTS hive.lake.players (
    puuid VARCHAR,
    tier VARCHAR,
    queue VARCHAR,
    league_id VARCHAR,
    league_name VARCHAR,
    rank VARCHAR,
    league_points INT,
    wins INT,
    losses INT,
    veteran BOOLEAN,
    inactive BOOLEAN,
    fresh_blood BOOLEAN,
    hot_streak BOOLEAN,
    last_updated VARCHAR,
    region VARCHAR
)
WITH (
    external_location = 's3a://data-lakehouse/raw/players/',
    format = 'JSON',
    partitioned_by = ARRAY['region']
);

CREATE SCHEMA IF NOT EXISTS hive.warehouse;

CREATE TABLE IF NOT EXISTS hive.warehouse.matches (
    match_id VARCHAR,
    team1_champions VARCHAR,
    team2_champions VARCHAR,
    team1_win VARCHAR,
    game_start VARCHAR,
    game_date VARCHAR,
    date VARCHAR
)
WITH (
    external_location = 's3a://data-lakehouse/curated/matches/',
    format = 'CSV',
    partitioned_by = ARRAY['date'],
    skip_header_line_count = 1
);
