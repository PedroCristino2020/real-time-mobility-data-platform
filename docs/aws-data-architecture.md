# AWS Data Architecture: S3 and Athena

## 1. Purpose

This document defines the proposed cloud storage and analytical architecture for the Real-Time Mobility Data Platform.

The objective is to extend the existing local BiciMAD pipeline with cloud storage and serverless SQL analytics while preserving the current local development workflow.

**Implementation status:** This document describes the target architecture. AWS S3, Glue Data Catalog and Athena integration are planned and are not considered implemented until deployed and tested.

## 2. Architecture Overview

The proposed data flow is:

1. Retrieve station information and station status from the BiciMAD GBFS API.
2. Store the original JSON responses in the Raw layer.
3. Transform and validate the data in the Silver layer.
4. Store structured historical station status data as date-partitioned Parquet files.
5. Calculate station-level availability metrics in the Gold layer using PySpark.
6. Upload the relevant datasets to Amazon S3.
7. Register the datasets in the AWS Glue Data Catalog.
8. Query the catalogued tables using Amazon Athena and SQL.

### Target Architecture

```text
BiciMAD GBFS API
        |
        v
Python Ingestion
        |
        v
   Raw Layer
   JSON files
        |
        v
Transformation and Data Quality
        |
        v
  Silver Layer
Partitioned Parquet
        |
        v
 PySpark Processing
        |
        v
   Gold Layer
Analytical Parquet
        |
        v
     Amazon S3
        |
        v
AWS Glue Data Catalog
        |
        v
   Amazon Athena
       SQL
```

The local pipeline remains available for development and testing. Cloud integration will be added as an optional stage.

## 3. Amazon S3 Storage Layout

The proposed bucket layout is:

```text
s3://<bucket-name>/
├── raw/
│   └── bicimad/
│       ├── station_information.json
│       └── station_status/
│           └── <timestamp>.json
├── silver/
│   └── bicimad/
│       ├── stations/
│       │   └── *.parquet
│       └── station_status/
│           └── year=YYYY/
│               └── month=MM/
│                   └── day=DD/
│                       └── *.parquet
└── gold/
    └── bicimad/
        └── station_availability/
            └── *.parquet
```

`<bucket-name>` is a placeholder and must be replaced with the actual S3 bucket name.

S3 uses object keys rather than physical directories. The prefixes above provide a logical organization for datasets and permissions.

### Raw Layer

The Raw layer preserves source responses in JSON format. Historical station status snapshots are stored separately so they can be inspected or reprocessed later.

### Silver Layer

The Silver layer contains structured and validated datasets. Parquet is used for analytical data because it is columnar and supports efficient queries.

Station status data is partitioned by the date of the snapshot. Station metadata is stored separately because it changes less frequently than operational status data.

### Gold Layer

The Gold layer contains station-level analytical metrics calculated by PySpark. The final schema and partitioning strategy will be confirmed against the implemented Gold output before deployment.

## 4. Partitioning Strategy

The initial partitioning strategy for historical station status data is:

| Partition column | Example | Purpose |
|---|---|---|
| `year` | `2026` | Filter by year |
| `month` | `10` | Filter by month |
| `day` | `19` | Filter by day |

Partition values are derived from the snapshot timestamp, not from the upload time.

The initial design does not partition by station ID. With hundreds of stations and frequent snapshots, partitioning by station could create excessive numbers of small files.

The pipeline should aim to avoid generating many tiny Parquet files. File sizes and partition granularity can be reviewed as the historical dataset grows.

## 5. AWS Glue Data Catalog

The AWS Glue Data Catalog will store metadata describing the datasets in S3.

The initial logical tables are:

| Proposed table | Dataset | Format |
|---|---|---|
| `bicimad_stations` | Silver station metadata | Parquet |
| `bicimad_station_status` | Historical station status | Parquet |
| `bicimad_station_availability` | Gold station-level metrics | Parquet |

These are proposed table names. Their schemas, S3 locations and partition definitions must match the actual datasets before the tables are created.

For the partitioned station status table, the catalog must expose the `year`, `month` and `day` partition columns consistently with the S3 object paths.

## 6. Amazon Athena

Amazon Athena will provide serverless SQL access to the datasets stored in S3.

The initial use cases include:

- Analysing historical bike availability.
- Comparing availability across stations and dates.
- Identifying stations with consistently low availability.
- Validating aggregate results against the local Gold dataset.

Example query, assuming the catalog table and column names have been confirmed:

```sql
SELECT
    station_id,
    AVG(available_bikes) AS avg_available_bikes
FROM bicimad_station_status
WHERE year = '2026'
  AND month = '10'
GROUP BY station_id
ORDER BY avg_available_bikes DESC;
```

This query is illustrative and must be adapted to the actual schema. Partition filters should be included when applicable to reduce the amount of data scanned.

## 7. Security and Cost Considerations

The implementation should follow these principles:

- Keep AWS credentials out of source code and Git.
- Use an AWS IAM identity with only the permissions required by the pipeline.
- Keep S3 buckets private unless public access is explicitly required.
- Configure the Athena query results location in S3.
- Monitor storage, requests and data scanned by Athena.
- Avoid running unnecessary queries against large historical datasets.
- Define a retention policy for raw snapshots and generated datasets where appropriate.

AWS costs depend on the services, storage volume, requests, region and query usage. Charges should be checked before enabling resources.

## 8. Implementation Plan

The cloud integration will be implemented incrementally:

1. Confirm AWS account access and configure secure credentials.
2. Create a private S3 bucket and define the required prefixes.
3. Add an optional Python upload stage using the AWS SDK.
4. Upload and verify a small sample of Parquet data.
5. Create Glue Data Catalog tables matching the real schemas.
6. Configure Athena query results storage and run validation queries.
7. Document the deployment and test results.

The local pipeline and automated tests must continue to work without requiring AWS credentials.

## 9. Current Status

The local project already includes BiciMAD ingestion, Raw and Silver processing, data quality checks, Parquet generation, PySpark analytics, automated tests and CI checks.

The S3, Glue Data Catalog and Athena components described here are planned extensions. Their implementation status will be updated after each component has been deployed and verified.