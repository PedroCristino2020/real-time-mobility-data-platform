# Learning Log

## 2026-10-01 — BiciMAD ingestion pipeline

### Objective

Build the first real ingestion pipeline for the project using BiciMAD mobility data.

### What I implemented

- Connected to the BiciMAD GBFS API using Python and `requests`.
- Identified the `station_information` and `station_status` feeds.
- Stored the original API responses as raw JSON.
- Created timestamped snapshots for `station_status`.
- Created a Silver transformation selecting relevant station fields.
- Added data quality checks for:
  - missing station IDs
  - duplicate station snapshots
  - negative bike values
  - negative dock values
  - invalid status values
  - missing timestamps
- Changed duplicate detection to use `(snapshot_timestamp, station_id)` because the same station is expected to appear in multiple snapshots.
- Separated relatively static `station_information` from periodically changing `station_status`.
- Implemented a Python scheduler to capture `station_status` every 5 minutes.
- Organized the ingestion scripts as a Python package.

### Important design decisions

#### Raw vs Silver

Raw data is kept unchanged to preserve the original source data.

Silver data contains only the fields required for analysis and downstream processing.

#### Station information vs station status

`station_information` contains relatively static station metadata, so it does not need to be downloaded every five minutes.

`station_status` changes continuously and is therefore captured periodically.

#### Timestamped snapshots

Each `station_status` response is stored with a UTC timestamp in the filename.

This allows the platform to build a historical time series instead of only keeping the latest state.

#### Data quality

The pipeline validates the transformed data before it is used downstream.

One unexpected status value (`NOT_IN_SERVICE`) was detected during validation and the validation rules were updated after checking the actual source data.

### Current result

The pipeline successfully captures BiciMAD station status data periodically and transforms multiple snapshots into Silver data.

Each snapshot contains approximately 678 stations.

### Concepts learned

- REST APIs
- HTTP requests
- JSON
- Python `requests`
- `pathlib` / `os.path`
- timestamps and UTC
- raw vs transformed data
- ETL
- data quality validation
- incremental snapshots
- Python packages and relative imports
- scheduled ingestion