-- Athena / AWS Glue Data Catalog DDL: historical station status.
--
-- This table is compatible with the local S3 layout:
--     s3://<bucket-name>/silver/bicimad/station_status/date=YYYY-MM-DD/*.parquet
--
-- The DDL is an artifact that can be executed in Athena when an AWS account is
-- available. It is not required by the local pipeline, which validates the same
-- logic for free with DuckDB (see sql/duckdb/station_queries.sql).
--
-- Replace <bucket-name> with the real bucket before running in AWS.

CREATE EXTERNAL TABLE IF NOT EXISTS bicimad_station_status (
    snapshot_timestamp  timestamp,
    station_id          string,
    num_bikes_available bigint,
    num_bikes_disabled  bigint,
    num_docks_available bigint,
    num_docks_disabled  bigint,
    status              string,
    is_renting          boolean,
    is_returning        boolean,
    last_reported       bigint
)
PARTITIONED BY (date string)
STORED AS PARQUET
LOCATION 's3://<bucket-name>/silver/bicimad/station_status/'
TBLPROPERTIES (
    'parquet.compression' = 'SNAPPY',
    'projection.enabled' = 'true',
    'projection.date.type' = 'date',
    'projection.date.range' = '2024-01-01,NOW',
    'projection.date.format' = 'yyyy-MM-dd',
    'projection.date.interval' = '1',
    'projection.date.interval.unit' = 'DAYS',
    'storage.location.template' = 's3://<bucket-name>/silver/bicimad/station_status/date=${date}/'
);
