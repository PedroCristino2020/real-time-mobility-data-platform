# Athena Queries and Cost-Aware SQL

The queries below target the tables created by `sql/athena/*.sql`. They are
written for Amazon Athena, but the same logic is validated locally and for free
with DuckDB (`sql/duckdb/station_queries.sql`).

Athena charges by the amount of data scanned, so the two most important habits
are:

1. **Partition pruning:** always filter on the partition column.
2. **Column projection:** select only the columns you need instead of `SELECT *`.

## 1. Partition pruning

```sql
SELECT
    station_id,
    ROUND(AVG(num_bikes_available), 2) AS avg_bikes_available
FROM bicimad_station_status
WHERE date = '2026-10-01'
GROUP BY station_id
ORDER BY avg_bikes_available DESC
LIMIT 10;
```

`WHERE date = '...'` restricts the scan to a single `date=YYYY-MM-DD`
partition. Without that filter Athena reads every historical partition.

For a range of dates:

```sql
SELECT
    date,
    ROUND(AVG(num_bikes_available), 2) AS avg_bikes_available
FROM bicimad_station_status
WHERE date BETWEEN '2026-10-01' AND '2026-10-19'
GROUP BY date
ORDER BY date;
```

## 2. Column projection

```sql
SELECT
    snapshot_timestamp,
    station_id,
    num_bikes_available
FROM bicimad_station_status
WHERE date = '2026-10-01'
  AND status = 'IN_SERVICE'
ORDER BY snapshot_timestamp DESC
LIMIT 20;
```

Only the three projected columns are read from Parquet, which reduces the
amount of data scanned compared with `SELECT *`.

## 3. Aggregation with station metadata

```sql
SELECT
    s.station_id,
    s.name,
    s.capacity,
    ROUND(AVG(st.num_bikes_available), 2) AS avg_bikes,
    COUNT(*) AS snapshots
FROM bicimad_station_status AS st
JOIN bicimad_stations AS s
    ON s.station_id = st.station_id
WHERE st.date BETWEEN '2026-10-01' AND '2026-10-19'
GROUP BY s.station_id, s.name, s.capacity
ORDER BY avg_bikes DESC
LIMIT 10;
```

## 4. CTAS: materialise a reusable aggregate

`CREATE TABLE AS SELECT` (CTAS) writes the result to S3 in Parquet so it can be
reused without rescanning the raw history:

```sql
CREATE TABLE bicimad_station_daily_metrics
WITH (
    format = 'PARQUET',
    external_location = 's3://<bucket-name>/gold/bicimad/station_daily_metrics/',
    partitioned_by = ARRAY['date']
) AS
SELECT
    date,
    station_id,
    ROUND(AVG(num_bikes_available), 2) AS avg_bikes_available,
    ROUND(AVG(num_docks_available), 2) AS avg_docks_available,
    COUNT(*) AS snapshot_count
FROM bicimad_station_status
WHERE date BETWEEN '2026-10-01' AND '2026-10-19'
GROUP BY date, station_id;
```

## 5. Gold availability metrics

```sql
SELECT
    station_id,
    name,
    availability_percentage
FROM bicimad_station_availability
ORDER BY availability_percentage DESC
LIMIT 10;
```

## 6. Quality metrics

The quality report is written to
`s3://<bucket-name>/gold/bicimad/quality_metrics/`. Register
`quality_summary.parquet` and `column_completeness.parquet` in the catalogue and
query them like any other Parquet dataset:

```sql
SELECT
    generated_at,
    record_count,
    total_rule_issues,
    is_fresh,
    passed
FROM bicimad_quality_summary
ORDER BY generated_at DESC
LIMIT 10;
```

```sql
SELECT
    column,
    missing,
    completeness
FROM bicimad_column_completeness
ORDER BY completeness ASC;
```

## 7. Iceberg time travel

When the Iceberg table from `sql/athena/create_iceberg_tables.sql` is available:

```sql
-- Inspect the snapshot history.
SELECT * FROM "bicimad_station_status_iceberg$snapshots"
ORDER BY committed_at DESC;

-- Query the table as it was one day ago.
SELECT station_id, AVG(num_bikes_available) AS avg_bikes
FROM bicimad_station_status_iceberg
FOR TIMESTAMP AS OF (current_timestamp - interval '1' day)
GROUP BY station_id;
```

## 8. Cost, latency and scan notes

| Practice | Effect |
|---|---|
| Filter on `date` | Reads only the selected partitions. |
| Select explicit columns | Reads only the required column chunks. |
| Use `LIMIT` while exploring | Avoids returning more rows than needed. |
| Materialise with CTAS | Avoids rescanning raw history for repeated reports. |
| Keep files reasonably large | Reduces per-file overhead and improves throughput. |
| Use Iceberg compaction | Avoids the small-file problem after many appends. |
| Expire old snapshots | Controls metadata growth and storage cost. |

## 9. Local validation (free)

DuckDB runs the same query patterns against the local Parquet files:

```bash
python -m governance.run_local_queries
```

The SQL lives in `sql/duckdb/station_queries.sql` and uses `read_parquet()`
instead of catalogue tables. This keeps the project runnable without an AWS
account or paid services.

## 10. Applying the DDL in Athena

Only needed when an AWS account is available:

1. Replace `<bucket-name>` in `sql/athena/*.sql`.
2. Run the DDL in the Athena query editor.
3. Configure an S3 location for query results.
4. Run the queries above and compare the results with the local Gold dataset.

AWS charges for S3 storage/requests and for the data scanned by Athena. Review
the pricing before running queries against large datasets.
