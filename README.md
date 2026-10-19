# Real-Time Mobility Data Platform

An end-to-end Data Engineering portfolio project built around real-world bike-sharing data from BiciMAD in Madrid, Spain.

The platform ingests mobility data from the BiciMAD GBFS API, validates data quality, transforms historical snapshots into analytical datasets and generates station-level availability metrics using Python and PySpark. It also integrates local S3-compatible object storage to demonstrate a storage workflow without requiring an AWS deployment.

## Architecture

The project follows a layered data architecture:

- **Raw:** stores the original GBFS station information and timestamped station-status snapshots.
- **Silver:** transforms source data into structured datasets, applies data quality checks and stores historical status data in date-partitioned Parquet files.
- **Gold:** generates station-level availability metrics using PySpark and stores the resulting analytical dataset.

The project also uses a local S3-compatible storage service, managed with Docker Compose, to store processed analytical data.

### Pipeline Workflow

1. **Data ingestion:** retrieves station information and current station status from the BiciMAD GBFS API.
2. **Data transformation:** extracts station metadata and consolidates historical station-status snapshots.
3. **Data quality:** checks for missing station IDs and timestamps, duplicate snapshots, negative bike or dock counts, invalid status values and missing numeric fields.
4. **Parquet conversion:** stores historical station-status data in date-partitioned Parquet files.
5. **Analytical processing:** uses PySpark to calculate average bike and dock availability, snapshot counts and availability rates for each station.
6. **Object storage:** uploads processed datasets to a local S3-compatible object storage service.
7. **Automation:** the pipeline is designed to execute repeatedly at five-minute intervals, logging failures so that the recurring execution loop can continue.

## Tech Stack

| Category | Technologies |
|---|---|
| Programming language | Python |
| Data processing | pandas, PySpark |
| Storage formats | JSON, Parquet |
| Data source | BiciMAD GBFS API |
| Object storage | S3-compatible local storage, Docker Compose |
| Testing | pytest |
| Code quality | Ruff |
| Continuous integration | GitHub Actions |
| Version control | Git, GitHub |

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

Run the checks locally:

```bash
python -m ruff check .
python -m pytest -v
```

**Latest verified results:** all eight tests passed, and Ruff reported no issues.

## Repository Structure

```text
real-time-mobility-data-platform/
├── .github/
│   └── workflows/
│       └── tests.yml
├── dashboard/
├── data/
│   ├── raw/
│   ├── silver/
│   └── gold/
├── docs/
├── etl/
├── ingestion/
├── spark/
├── sql/
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
- Eight passing automated tests.
- Successful Ruff checks.
- GitHub Actions configured to run code quality checks and tests on pushes and pull requests targeting `main`.

The local S3-compatible storage integration provides an additional object-storage workflow. It does not represent a deployment to AWS.

## Planned Improvements

- Develop a dashboard for exploring station availability and historical trends.
- Integrate additional mobility data sources.
- Extend temporal analysis to identify usage patterns by hour and day.
- Explore cloud storage and querying with AWS S3, AWS Glue and Athena.
- Improve deployment and reproducibility.
- Investigate natural-language analytics using Large Language Models (LLMs).
