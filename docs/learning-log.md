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

## 2026-10-02 — Silver Parquet and Gold metrics

### What I implemented

- Converted BiciMAD Silver data from JSON to Parquet using pandas and PyArrow.
- Partitioned station status data by date.
- Created the first Gold dataset for analytical use.
- Joined station status data with station metadata.
- Calculated the average bike availability rate for each station.
- Converted the availability rate into a percentage.
- Validated the resulting Gold dataset.

### Gold dataset

The Gold dataset contains one record per BiciMAD station with:

- station ID
- station name
- station capacity
- average availability rate
- average availability percentage

The resulting dataset contains 678 stations.

### Concepts learned

- Parquet
- Data partitioning
- Silver to Gold transformations
- Dataset joins
- Business metrics
- Aggregations with pandas
- Analytical datasets

## 2026-10-04 — PySpark processing pipeline

### What I implemented

- Configured PySpark to run correctly on Windows.
- Read the Silver BiciMAD Parquet dataset using PySpark.
- Loaded station metadata from JSON using Spark.
- Aggregated station data using `groupBy`, `avg` and `count`.
- Calculated the average number of available bikes and docks per station.
- Calculated the station availability rate.
- Joined the aggregated data with station metadata using `join`.
- Generated a Gold analytical dataset using PySpark.
- Saved the Gold dataset as Parquet.
- Added validation checks for the generated Gold dataset.

### PySpark processing

The PySpark pipeline reads the Silver BiciMAD dataset containing 8,136 records from 12 snapshots of 678 stations.

For each station, the pipeline calculates:

- Average available bikes.
- Average available docks.
- Number of snapshots.
- Availability rate.
- Availability percentage.

The aggregated metrics are then joined with station metadata to include the station name and capacity.

### Gold dataset

The PySpark Gold dataset contains 678 records, one per station, with:

- station ID
- average available bikes
- average available docks
- snapshot count
- availability rate
- station name
- capacity
- availability percentage

The Gold dataset is stored as Parquet at:

`data/gold/bicimad/station_availability_spark`

### Data validation

The generated Gold dataset was validated using PySpark:

- 678 Gold records.
- 0 null station IDs.
- 0 availability percentages outside the range 0–100%.
- 12 snapshots per station.

### Concepts learned

- PySpark DataFrames
- SparkSession
- Reading and writing Parquet with Spark
- `groupBy` and aggregations
- `avg` and `count`
- DataFrame joins
- Derived metrics
- Spark-based data validation
- Silver → Gold transformations
- Distributed data processing concepts
- Running PySpark locally on Windows