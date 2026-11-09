# Apache Iceberg Design (Local and Athena)

## 1. Purpose

The Silver station-status dataset is currently stored as date-partitioned
Parquet. Apache Iceberg adds:

- **Hidden partitioning** (queries do not need to know the physical partition
  columns).
- **Snapshots and time travel** (query the table as it was at a given time).
- **Schema evolution** without rewriting the full dataset.
- **Safe compaction** (`rewrite_data_files`) to avoid small files.
- **Snapshot expiry** (`expire_snapshots`) to control metadata growth.

## 2. Table design

| Property | Value |
|---|---|
| Table | `bicimad.station_status` |
| Format | Parquet |
| Partition transform | `days(snapshot_timestamp)` |
| Target file size | 128 MB (`write.target-file-size-bytes = 134217728`) |
| Catalog (local) | Hadoop filesystem catalog |
| Catalog (AWS) | Glue Data Catalog |
| Warehouse (local) | `data/iceberg_warehouse` |

The schema matches the Silver Parquet dataset:

```text
snapshot_timestamp  timestamp
station_id          string
num_bikes_available bigint
num_bikes_disabled  bigint
num_docks_available bigint
num_docks_disabled  bigint
status              string
is_renting          boolean
is_returning        boolean
last_reported       bigint
```

`days(snapshot_timestamp)` is a hidden partition: analysts filter by
`snapshot_timestamp` and Iceberg prunes the matching days automatically.

## 3. Why not partition by station

With hundreds of stations and a snapshot every five minutes, partitioning by
`station_id` would create a very large number of small files. The date-based
transform keeps files reasonably large and still allows efficient time-range
queries.

## 4. Snapshots and time travel

Every write creates a new snapshot. The snapshot history can be inspected with:

```sql
SELECT snapshot_id, committed_at, operation
FROM local.bicimad.station_status.snapshots
ORDER BY committed_at DESC;
```

Time travel (Athena syntax):

```sql
SELECT *
FROM bicimad_station_status_iceberg
FOR TIMESTAMP AS OF (current_timestamp - interval '1' day);
```

## 5. Maintenance

| Operation | Purpose | How |
|---|---|---|
| Compaction | Merge small files into ~128 MB files. | `rewrite_data_files` / Athena `OPTIMIZE`. |
| Snapshot expiry | Remove old snapshots and orphan files. | `expire_snapshots` procedure. |
| Orphan file cleanup | Delete files no longer referenced. | `remove_orphan_files` procedure. |

Iceberg metadata must **not** be expired with S3 lifecycle rules: deleting
metadata files directly can corrupt the table. Use the Iceberg procedures
instead. The S3 lifecycle policy in `infra/s3_lifecycle.json` deliberately does
not target Iceberg metadata.

## 6. Local execution (free)

`spark/iceberg_write_example.py` creates and queries the table locally:

```bash
python -m spark.iceberg_write_example
```

How it works:

1. Spark 3.5 is configured with the Iceberg Spark runtime.
2. A Hadoop catalog named `local` points to `data/iceberg_warehouse`.
3. A temporary view reads the Silver Parquet dataset.
4. `CREATE OR REPLACE TABLE ... USING iceberg PARTITIONED BY
   (days(snapshot_timestamp))` writes the table.
5. The script prints the top stations by average bikes, the snapshot history
   and the partition metadata.

The first run downloads the Iceberg runtime from Maven Central, so it needs
internet access. The example is not part of the default pipeline or the CI test
suite.

## 7. Athena DDL

`sql/athena/create_iceberg_tables.sql` contains the equivalent Athena DDL. It
is an artifact ready to run when an AWS account is available:

- `PARTITIONED BY (day(snapshot_timestamp))`
- `table_type = 'ICEBERG'`
- `vacuum_min_snapshots_to_keep = 5`
- `vacuum_max_snapshot_age_seconds = 604800`
- `optimize_rewrite_data_file_threshold = 10`

## 8. Status

| Component | Local status | AWS status |
|---|---|---|
| Iceberg table design | Implemented | Artifact ready |
| Local Hadoop catalog | Runnable example | — |
| Athena Iceberg DDL | — | Not deployed (requires AWS) |
| Compaction/expiry | Documented | Not applied |

The local example and the Athena DDL demonstrate the design without deploying
paid AWS resources.
