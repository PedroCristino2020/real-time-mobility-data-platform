-- Athena / AWS Glue Data Catalog DDL: Silver station metadata.
--
-- This table is compatible with the local S3 layout:
--     s3://<bucket-name>/silver/bicimad/stations/stations.parquet
-- Replace <bucket-name> before running in AWS.

CREATE EXTERNAL TABLE IF NOT EXISTS bicimad_stations (
    station_id          string,
    name                string,
    lat                 double,
    lon                 double,
    address             string,
    capacity            bigint,
    is_charging_station boolean,
    is_virtual_station  boolean
)
STORED AS PARQUET
LOCATION 's3://<bucket-name>/silver/bicimad/stations/'
TBLPROPERTIES ('parquet.compression' = 'SNAPPY');
