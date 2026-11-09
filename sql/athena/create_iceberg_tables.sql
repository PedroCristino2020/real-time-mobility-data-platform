-- Athena DDL: Apache Iceberg version of the historical station status table.
--
-- The equivalent local, free execution is implemented in
-- spark/iceberg_write_example.py with a Hadoop (filesystem) catalog. The AWS
-- DDL below is an artifact ready to be executed when an AWS account is
-- available; it is not applied by the local pipeline.
--
-- Replace <bucket-name> with the real bucket before running in AWS.

CREATE TABLE IF NOT EXISTS bicimad_station_status_iceberg (
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
PARTITIONED BY (day(snapshot_timestamp))
LOCATION 's3://<bucket-name>/silver/bicimad/station_status_iceberg/'
TBLPROPERTIES (
    'table_type' = 'ICEBERG',
    'format' = 'parquet',
    'write_target_file_size_bytes' = '134217728',
    'vacuum_min_snapshots_to_keep' = '5',
    'vacuum_max_snapshot_age_seconds' = '604800',
    'optimize_rewrite_data_file_threshold' = '10',
    'optimize_rewrite_delete_file_threshold' = '10'
);

-- Example snapshot history inspection (Athena Iceberg syntax).
-- SELECT * FROM "bicimad_station_status_iceberg$snapshots" ORDER BY committed_at DESC;

-- Example time-travel query (Athena Iceberg syntax).
-- SELECT * FROM bicimad_station_status_iceberg
-- FOR TIMESTAMP AS OF (current_timestamp - interval '1' day);
