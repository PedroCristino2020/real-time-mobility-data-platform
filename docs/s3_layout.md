# S3 Storage Layout and Dataset Metadata

This document defines how datasets are organised, named and described. The
same convention is used by the local S3-compatible storage (MinIO/Silo) and can
be ported to Amazon S3 without changing the pipeline code.

## 1. Bucket and prefixes

```text
s3://mobility-data/
├── raw/
│   └── bicimad/
│       ├── station_information.json
│       └── station_status/
│           └── <YYYY-MM-DD_HH-MM-SS>.json
├── silver/
│   └── bicimad/
│       ├── stations.json
│       └── station_status/
│           └── date=YYYY-MM-DD/
│               └── station_status.parquet
├── gold/
│   └── bicimad/
│       ├── station_availability_spark/
│       │   └── *.parquet
│       └── quality_metrics/
│           ├── quality_metrics_<timestamp>.json
│           ├── latest.json
│           ├── quality_summary.parquet
│           ├── column_completeness.parquet
│           └── rule_issues.parquet
├── _metadata/
│   ├── catalog.json
│   └── <dataset>.json
└── athena-results/
```

The bucket name is configurable in `config/datasets.json` (default:
`mobility-data`). S3 uses object keys rather than real directories; the prefixes
above provide a logical organisation for permissions, lifecycle rules and
catalogue tables.

## 2. Naming conventions

| Element | Convention | Example |
|---|---|---|
| Layer | `raw`, `silver`, `gold` | `silver` |
| Source system | lowercase, no spaces | `bicimad` |
| Dataset | lowercase, snake_case | `station_status` |
| Partition key | `date=YYYY-MM-DD` | `date=2026-10-01` |
| Raw snapshot | `<YYYY-MM-DD_HH-MM-SS>.json` | `2026-10-15_16-51-14.json` |
| Manifest | `<dataset>.json` | `silver_station_status.json` |

The machine-readable version of these rules lives in `config/datasets.json`
under `naming`.

## 3. Partitioning

Historical station status is partitioned by the snapshot date:

```text
silver/bicimad/station_status/date=2026-10-01/station_status.parquet
```

Partition values are derived from `snapshot_timestamp` (UTC), not from the
upload time. Date partitions keep files reasonably large and allow Athena,
DuckDB and Spark to prune the data they read.

The project deliberately does **not** partition by `station_id`: with hundreds
of stations and a snapshot every five minutes it would create a very large
number of small files.

## 4. Dataset manifests

`config/datasets.json` declares every dataset (layer, path, format, source,
schema version, freshness SLA, partitions and tags). The manifest generator
enriches that definition with live statistics:

```bash
python -m governance.dataset_metadata
python -m governance.dataset_metadata --upload
```

Output:

- `data/_metadata/<dataset>.json` — one manifest per dataset.
- `data/_metadata/catalog.json` — aggregate catalogue.
- `_metadata/<dataset>.json` — the same files uploaded to the S3-compatible
  storage when `--upload` is used.

Each manifest contains:

```json
{
  "dataset": "silver_station_status",
  "layer": "silver",
  "format": "parquet",
  "location": {
    "local_path": "data/silver/bicimad/station_status",
    "s3_uri": "s3://mobility-data/silver/bicimad/station_status"
  },
  "source": "BiciMAD GBFS station_status feed",
  "owner": "Pedro Cristino Moreno",
  "schema_version": "1.0",
  "freshness_sla_minutes": 15,
  "partition_columns": ["date"],
  "partition_pattern": "date=YYYY-MM-DD",
  "tags": {
    "project": "bicimad-mobility",
    "environment": "local",
    "data_classification": "public",
    "managed_by": "python-pipeline",
    "update_frequency": "5-minutes"
  },
  "generated_at": "2026-11-09T00:00:00+00:00",
  "exists": true,
  "size_bytes": 0,
  "row_count": 8136,
  "columns": ["snapshot_timestamp", "station_id"],
  "partitions": ["date=2026-10-01"],
  "file_count": 3
}
```

## 5. Tagging

The default tags are inherited from `config/datasets.json` and can be
overridden per dataset:

| Tag | Purpose |
|---|---|
| `project` | Groups resources of the same data product. |
| `environment` | `local` today; `dev`/`prod` if deployed. |
| `data_classification` | `public` for the BiciMAD open data. |
| `managed_by` | Identifies the pipeline that owns the data. |
| `update_frequency` | Expected refresh cadence. |

When moving to AWS, the same key/value pairs can be applied as S3 object tags
or bucket tags and as Glue table parameters.

## 6. Lifecycle policy

`infra/s3_lifecycle.json` is a portable S3 lifecycle configuration:

| Rule | Scope | Action |
|---|---|---|
| `transition-raw-to-infrequent-access` | `raw/` | Standard-IA after 30 days, Glacier Instant Retrieval after 90 days. |
| `expire-raw-status-snapshots` | `raw/bicimad/station_status/` | Expire after 365 days; clean noncurrent versions and incomplete multipart uploads. |
| `expire-athena-query-results` | `athena-results/` | Expire after 30 days. |
| `expire-quality-metrics-history` | `gold/bicimad/quality_metrics/` | Expire after 180 days. |

The policy is an artifact and is **not applied** to any AWS bucket by this
project. Applying it in AWS requires an account and may generate charges.

Notes:

- `NoncurrentVersionExpiration` only has effect when bucket versioning is
  enabled.
- Iceberg snapshots and metadata must be expired with Iceberg procedures
  (`expire_snapshots`, `rewrite_data_files`), not with S3 lifecycle rules,
  because deleting metadata files directly can corrupt the table.

## 7. Portability to AWS

The local pipeline already writes the same object keys that the Athena DDL
expects. To move to AWS:

1. Create a private bucket and keep credentials out of Git.
2. Upload the existing prefixes with the AWS SDK or `aws s3 sync`.
3. Replace `<bucket-name>` in `sql/athena/*.sql`.
4. Register the tables in the Glue Data Catalog and run the queries in
   `docs/athena_queries.md`.
5. Apply `infra/s3_lifecycle.json` only after reviewing the retention policy.

The local workflow and the automated tests continue to work without AWS
credentials.
