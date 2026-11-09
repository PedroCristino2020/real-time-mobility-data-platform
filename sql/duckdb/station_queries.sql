-- Local DuckDB validation queries.
--
-- These queries mirror the Athena queries in docs/athena_queries.md but use
-- DuckDB's read_parquet() so they run for free against the local files.
--
-- Query 1: partition pruning. Only the requested date partition is read.
SELECT
    station_id,
    ROUND(AVG(num_bikes_available), 2) AS avg_bikes_available
FROM read_parquet(
    'data/silver/bicimad/station_status/date=2026-11-09/*.parquet'
)
GROUP BY station_id
ORDER BY avg_bikes_available DESC
LIMIT 10;

-- Query 2: column projection. Only the required columns are read.
SELECT
    snapshot_timestamp,
    station_id,
    num_bikes_available
FROM read_parquet(
    'data/silver/bicimad/station_status/*/*.parquet',
    hive_partitioning = true
)
WHERE status = 'IN_SERVICE'
ORDER BY snapshot_timestamp DESC
LIMIT 20;

-- Query 3: join with station metadata.
SELECT
    s.station_id,
    s.name,
    s.capacity,
    ROUND(AVG(st.num_bikes_available), 2) AS avg_bikes,
    COUNT(*) AS snapshots
FROM read_parquet(
    'data/silver/bicimad/station_status/*/*.parquet',
    hive_partitioning = true
) AS st
JOIN read_parquet('data/silver/bicimad/stations/stations.parquet') AS s
    ON s.station_id = st.station_id
GROUP BY s.station_id, s.name, s.capacity
ORDER BY avg_bikes DESC
LIMIT 10;

-- Query 4: Gold availability metrics.
SELECT
    station_id,
    name,
    availability_percentage
FROM read_parquet(
    'data/gold/bicimad/station_availability_spark/*.parquet'
)
ORDER BY availability_percentage DESC
LIMIT 10;

-- Query 5: CTAS pattern. Materialise a daily aggregate for reuse.
CREATE OR REPLACE TEMP TABLE station_daily_metrics AS
SELECT
    date,
    station_id,
    ROUND(AVG(num_bikes_available), 2) AS avg_bikes_available,
    ROUND(AVG(num_docks_available), 2) AS avg_docks_available,
    COUNT(*) AS snapshot_count
FROM read_parquet(
    'data/silver/bicimad/station_status/*/*.parquet',
    hive_partitioning = true
)
GROUP BY date, station_id;

SELECT *
FROM station_daily_metrics
ORDER BY date, station_id
LIMIT 20;

-- Query 6: per-column completeness.
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE station_id IS NULL) AS missing_station_id,
    COUNT(*) FILTER (WHERE snapshot_timestamp IS NULL) AS missing_timestamp,
    COUNT(*) FILTER (WHERE num_bikes_available IS NULL) AS missing_bikes,
    COUNT(*) FILTER (WHERE num_docks_available IS NULL) AS missing_docks
FROM read_parquet(
    'data/silver/bicimad/station_status/*/*.parquet',
    hive_partitioning = true
);
