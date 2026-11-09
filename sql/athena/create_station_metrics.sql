-- Athena / AWS Glue Data Catalog DDL: Gold station availability metrics.
--
-- This table is compatible with the local S3 layout:
--     s3://<bucket-name>/gold/bicimad/station_availability_spark/*.parquet
--
-- The DDL is an artifact that can be executed in Athena when an AWS account is
-- available. Locally, the same dataset is queried for free with DuckDB (see
-- sql/duckdb/station_queries.sql).
--
-- Replace <bucket-name> with the real bucket before running in AWS.

CREATE EXTERNAL TABLE IF NOT EXISTS bicimad_station_availability (
    station_id             string,
    avg_bikes_available    double,
    avg_docks_available    double,
    snapshot_count         bigint,
    availability_rate      double,
    name                   string,
    capacity               bigint,
    availability_percentage double
)
STORED AS PARQUET
LOCATION 's3://<bucket-name>/gold/bicimad/station_availability_spark/'
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');
