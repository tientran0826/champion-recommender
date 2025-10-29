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
    external_location = 's3a://lake/players/',
    format = 'JSON',
    partitioned_by = ARRAY['region']
);
