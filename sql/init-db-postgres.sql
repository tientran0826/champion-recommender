-- Create databases for Dagster and Hive Metastore
CREATE DATABASE dagster_db;
CREATE DATABASE metastore;

-- Create users
CREATE USER dagster WITH ENCRYPTED PASSWORD 'dagster';
CREATE USER hive WITH ENCRYPTED PASSWORD 'hive';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE dagster_db TO dagster;
GRANT ALL PRIVILEGES ON DATABASE metastore TO hive;

-- Connect to dagster_db and grant schema privileges
\c dagster_db;
GRANT ALL ON SCHEMA public TO dagster;

-- Connect to metastore and grant schema privileges
\c metastore;
GRANT ALL ON SCHEMA public TO hive;
