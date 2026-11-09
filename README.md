# Real-Time Mobility Data Platform

An end-to-end Data Engineering portfolio project built around real-world bike-sharing data from BiciMAD in Madrid, Spain.

The platform ingests mobility data from the BiciMAD GBFS API, validates data quality, transforms historical snapshots into analytical datasets and generates station-level availability metrics using Python and PySpark. It also integrates local S3-compatible object storage to demonstrate a storage workflow without requiring an AWS deployment.

The project includes cloud-portable artifacts for Amazon S3, AWS Glue Data Catalog, Amazon Athena and Apache Iceberg. They are validated locally with open-source tools (DuckDB, PySpark and a Hadoop Iceberg catalog), so no paid AWS service is required.

## Architecture

The project follows a layered data architecture:

- **Raw:** stores the original GBFS station information and timestamped station-status snapshots.
- **Silver:** transforms source data into structured datasets, applies data quality checks and stores historical status data in date-partitioned Parquet files.
- **Gold:** generates station-level availability metrics using PySpark and stores the resulting analytical dataset.
- **Governance:** describes every dataset with a JSON manifest, monitors schema, completeness and freshness, and publishes quality metrics to the Gold layer.

The project also uses a local S3-compatible storage service, managed with Docker Compose, to store processed analytical data.

### Pipeline Workflow

1. **Data ingestion:** retrieves station information and current station status from the BiciMAD GBFS API.
2. **Data transformation:** extracts station metadata and consolidates historical station-status snapshots.
3. **Parquet conversion:** stores station metadata and historical station-status data as Parquet.
4. **Data quality:** checks for missing station IDs and timestamps, duplicate snapshots, negative bike or dock counts, invalid status values and missing numeric fields.
5. **Quality metrics:** validates the schema, calculates per-column completeness and compares the latest snapshot with the freshness SLA.
6. **Analytical processing:** uses PySpark to calculate average bike and dock availability, snapshot counts and availability rates for each station.
7. **Object storage:** uploads processed datasets, quality metrics and dataset manifests to a local S3-compatible object storage service.
8. **Metadata:** refreshes the JSON manifest of every dataset with live row counts, columns and partitions.
9. **Automation:** the pipeline is designed to execute repeatedly at five-minute intervals, logging failures so that the recurring execution loop can continue.

## Tech Stack

| Category | Technologies |
|---|---|
| Programming language | Python |
| Data processing | pandas, PySpark |
| Storage formats | JSON, Parquet, Apache Iceberg (local example) |
| Data source | BiciMAD GBFS API |
| Object storage | S3-compatible local storage, Docker Compose |
| Local SQL validation | DuckDB |
| Cloud-portable artifacts | AWS S3 layout, Glue Data Catalog DDL, Athena DDL, S3 lifecycle JSON, Iceberg DDL |
| Data governance | Dataset manifests, schema validation, completeness, freshness/SLA, quality metrics |
| Testing | pytest |
| Code quality | Ruff |
| Continuous integration | GitHub Actions |
| Version control | Git, GitHub |

## Data Governance and Metadata

`config/datasets.json` declares every dataset (layer, path, format, source, schema version, freshness SLA, partitions and tags). The manifest generator adds live statistics:

```bash
python -m governance.dataset_metadata
python -m governance.dataset_metadata --upload
```

Output:

- `data/_metadata/<dataset>.json`: one manifest per dataset.
- `data/_metadata/catalog.json`: aggregate catalogue.
- `_metadata/<dataset>.json`: uploaded to the S3-compatible storage with `--upload`.

See `docs/s3_layout.md` for the bucket/prefix convention, naming rules, partitioning and tagging.

## Cloud-Portable Artifacts (No Paid AWS Required)

The following artifacts describe the AWS target architecture. They are not deployed by the local pipeline and do not require an AWS account:

| Artifact | Location | Purpose |
|---|---|---|
| S3 layout and naming | `config/datasets.json`, `docs/s3_layout.md` | Bucket/prefix convention, partitioning, tagging and metadata. |
| S3 lifecycle policy | `infra/s3_lifecycle.json` | Transition, expiration and multipart cleanup rules. |
| Glue/Athena DDL | `sql/athena/*.sql` | External Parquet tables and Iceberg table definition. |
| Athena query guide | `docs/athena_queries.md` | Partition pruning, column projection, CTAS and cost notes. |
| Iceberg design | `docs/iceberg_design.md` | Hidden partitioning, snapshots, compaction and expiry. |
| Local Iceberg example | `spark/iceberg_write_example.py` | Creates and queries an Iceberg table with a Hadoop catalog. |
| Local SQL validation | `sql/duckdb/station_queries.sql`, `governance/run_local_queries.py` | Runs the same query patterns for free with DuckDB. |

## Data Quality and Testing

The project includes automated data quality checks and unit tests covering:

- Valid records
- Missing station IDs
- Duplicate station snapshots
- Negative bike counts
- Negative dock counts
- Invalid station status values
- Missing timestamps
- Missing numeric values
- Schema validation (missing, unexpected and mistyped columns)
- Per-column completeness
- Freshness/SLA detection
- Quality metrics output (JSON and Parquet)
- Dataset manifest generation

Run the checks locally:

```bash
python -m ruff check .
python -m pytest -v
```

Run only the extended quality report:

```bash
python -m governance.quality_metrics
```

See `docs/data_quality.md` for the full list of rules, the metrics schema and the quality gate.

## Repository Structure

```text
real-time-mobility-data-platform/
├── .github/
│   └── workflows/
│       └── tests.yml
├── config/
│   └── datasets.json
├── dashboard/
├── data/
│   ├── raw/
│   ├── silver/
│   ├── gold/
│   └── _metadata/          # generated manifests
├── docs/
│   ├── athena_queries.md
│   ├── aws-data-architecture.md
│   ├── data_quality.md
│   ├── iceberg_design.md
│   ├── learning-log.md
│   └── s3_layout.md
├── etl/
├── governance/
│   ├── dataset_metadata.py
│   ├── quality_metrics.py
│   └── run_local_queries.py
├── infra/
│   └── s3_lifecycle.json
├── ingestion/
├── spark/
│   └── iceberg_write_example.py
├── sql/
│   ├── athena/
│   └── duckdb/
├── tests/
├── .gitignore
├── architecture.md
├── docker-compose.yml
├── README.md
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python compatible with the project dependencies
- Java compatible with the installed PySpark version
- Docker Desktop with Docker Compose

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/PedroCristino2020/real-time-mobility-data-platform.git
cd real-time-mobility-data-platform
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

### Configure Object Storage

Configure the environment variables required by the storage integration in your local `.env` file, using the variable names expected by the project code.

Start the local S3-compatible storage service:

```bash
docker compose up -d
```

The service configuration is defined in `docker-compose.yml`. Keep credentials in `.env` and do not commit that file to GitHub.

### Run the Pipeline

From the project root, start the pipeline:

```bash
python -m ingestion.bicimad_pipeline
```

When running in recurring mode, the pipeline starts a new execution every five minutes. Stop it with `Ctrl+C`.

### Run Governance Tasks

```bash
# Refresh the dataset manifests.
python -m governance.dataset_metadata

# Compute the extended quality metrics.
python -m governance.quality_metrics

# Validate the Athena query patterns locally with DuckDB.
python -m governance.run_local_queries

# Optional: create an Iceberg table locally (downloads the Iceberg runtime).
python -m spark.iceberg_write_example
```

### Run Tests

```bash
python -m ruff check .
python -m pytest -v
```

To stop the local storage service when it is no longer needed:

```bash
docker compose down
```

This stops the containers but normally preserves data stored in the configured named volume.

## Current Status

The BiciMAD ingestion and processing pipeline has completed multiple consecutive runs successfully.

The latest previously verified processing results included:

- **678 stations** processed.
- A Gold dataset containing station-level availability metrics.
- No issues detected by the implemented data quality checks.
- 18 automated tests passing (data quality rules, schema validation, completeness, freshness and dataset manifests).
- Successful Ruff checks.
- GitHub Actions configured to run code quality checks and tests on pushes and pull requests targeting `main`.

The local S3-compatible storage integration provides an additional object-storage workflow. It does not represent a deployment to AWS.

The AWS S3, Glue, Athena and Iceberg artifacts are implemented and validated locally where possible. They are not deployed to AWS and do not consume paid services.

## Planned Improvements

- Develop a dashboard for exploring station availability and historical trends.
- Integrate additional mobility data sources.
- Extend temporal analysis to identify usage patterns by hour and day.
- Deploy the cloud artifacts to a real AWS account and validate them end to end.
- Improve deployment and reproducibility.
- Investigate natural-language analytics using Large Language Models (LLMs).
