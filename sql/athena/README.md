# Athena DDL

This directory contains AWS Athena / Glue Data Catalog DDL compatible with the
project's S3 layout. The DDL is an **artifact**: it is not executed by the local
pipeline and does not require an AWS account to keep the project working.

| File | Table | Dataset |
|---|---|---|
| `create_stations.sql` | `bicimad_stations` | Silver station metadata (Parquet). |
| `create_station_status.sql` | `bicimad_station_status` | Silver historical status (Parquet, partitioned by `date`). |
| `create_station_metrics.sql` | `bicimad_station_availability` | Gold station availability metrics (Parquet). |
| `create_iceberg_tables.sql` | `bicimad_station_status_iceberg` | Iceberg version with `day(snapshot_timestamp)` partitioning. |

## Before running in AWS

1. Replace `<bucket-name>` with the real bucket name.
2. Upload the datasets with the same prefixes used locally.
3. Configure an S3 location for Athena query results.
4. Run the DDL in the Athena query editor.
5. Run the queries from `docs/athena_queries.md`.

## Partition projection

`create_station_status.sql` enables partition projection for the `date`
partition:

```sql
'projection.enabled' = 'true',
'projection.date.type' = 'date',
'projection.date.range' = '2024-01-01,NOW',
'projection.date.format' = 'yyyy-MM-dd',
'projection.date.interval' = '1',
'projection.date.interval.unit' = 'DAYS',
'storage.location.template' = 's3://<bucket-name>/silver/bicimad/station_status/date=${date}/'
```

This avoids running `MSCK REPAIR TABLE` every time a new date partition is
written. A commented `MSCK REPAIR TABLE` statement is included for catalogues
where projection is disabled.

## Local validation (free)

The same query logic is validated locally with DuckDB:

```bash
python -m governance.run_local_queries
```

DuckDB reads the Parquet files directly, so no AWS account, Glue catalogue or
Athena query is required. The queries live in
`sql/duckdb/station_queries.sql`.

## Cost warning

Amazon Athena charges by the amount of data scanned, and S3 charges for storage
and requests. Review the pricing before running queries against large datasets.
The local DuckDB workflow is free and is the default validation path of this
project.
