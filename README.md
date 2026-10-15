# Real-Time Mobility Data Platform

An end-to-end Data Engineering portfolio project built around real-world bike-sharing data from BiciMAD in Madrid, Spain.

The platform ingests mobility data, validates its quality, transforms it into analytical datasets and generates station-level availability metrics using Python and PySpark.

## Architecture

The project follows a layered data architecture:

- **Raw:** stores the original GBFS station information and timestamped station-status snapshots.
- **Silver:** transforms source data into structured datasets, applies data quality checks and stores historical status data in date-partitioned Parquet files.
- **Gold:** generates station-level availability metrics using PySpark.

### Pipeline Workflow

1. **Data ingestion:** retrieves station information and current station status from the BiciMAD GBFS API.
2. **Data transformation:** extracts station metadata and consolidates historical station-status snapshots.
3. **Data quality:** detects missing station IDs and timestamps, duplicate snapshots, negative bike or dock counts, invalid status values and missing numeric fields.
4. **Parquet conversion:** stores historical station-status data in date-partitioned Parquet files.
5. **Analytical processing:** calculates average bike and dock availability, snapshot counts and availability rates for each station.
6. **Automation:** executes the pipeline every five minutes and logs failures while keeping the recurring execution loop running.

## Tech Stack

| Category | Technologies |
|---|---|
| Programming language | Python |
| Data processing | pandas, PySpark |
| Storage formats | JSON, Parquet |
| Data source | BiciMAD GBFS API |
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
├── README.md
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python
- Java compatible with the installed PySpark version

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/PedroCristino2020/real-time-mobility-data-platform.git
cd real-time-mobility-data-platform
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

### Run the Pipeline

Start the recurring BiciMAD pipeline from the project root:

```bash
python -m ingestion.bicimad_pipeline
```

The pipeline runs continuously, starting a new execution every five minutes. Stop it with `Ctrl+C`.

### Run Tests

```bash
python -m ruff check .
python -m pytest -v
```

## Current Status

The BiciMAD ingestion and processing pipeline has completed multiple consecutive runs successfully.

The latest verified processing run handled data for **678 stations**, generated a Gold dataset with station-level availability metrics and reported no issues in the implemented data quality checks.

The test suite and Ruff checks pass, and GitHub Actions is configured to run code quality checks and tests on pushes and pull requests targeting `main`.

## Planned Improvements

- Develop a dashboard for exploring station availability and historical trends.
- Integrate additional mobility data sources.
- Extend temporal analysis to identify usage patterns by hour and day.
- Explore cloud storage and querying with AWS S3 and Athena.
- Improve deployment and reproducibility.
- Investigate natural-language analytics using Large Language Models (LLMs).

---
