# Data Quality and Governance

The platform applies a quality gate to the Silver station-status dataset before
it is converted to Parquet and used to build the Gold metrics.

## 1. Rule-based checks

Implemented in `etl/bicimad_data_quality.py` and covered by
`tests/test_bicimad_data_quality.py`:

| Rule | Description |
|---|---|
| `missing_station_ids` | Records without a station identifier. |
| `duplicate_station_snapshots` | Duplicated `(snapshot_timestamp, station_id)` pairs. |
| `negative_bikes` | Negative `num_bikes_available`. |
| `negative_docks` | Negative `num_docks_available`. |
| `invalid_status_values` | Status outside `IN_SERVICE` / `NOT_IN_SERVICE`. |
| `missing_timestamps` | Records without `snapshot_timestamp`. |
| `missing_numeric_values` | Missing bike or dock counts. |

If the total number of rule issues is greater than zero, the pipeline stops
before publishing the Silver and Gold datasets.

## 2. Schema validation

Implemented in `governance/quality_metrics.py`. The expected logical schema is:

| Column | Type |
|---|---|
| `snapshot_timestamp` | timestamp (ISO-8601 string) |
| `station_id` | string |
| `num_bikes_available` | integer |
| `num_bikes_disabled` | integer |
| `num_docks_available` | integer |
| `num_docks_disabled` | integer |
| `status` | string |
| `is_renting` | boolean |
| `is_returning` | boolean |
| `last_reported` | integer |

The validator reports:

- `missing_columns`: expected columns not present in the records.
- `unexpected_columns`: columns not declared in the schema.
- `type_mismatches`: non-null values with an invalid logical type.

## 3. Completeness

For every expected column the report calculates the number of missing values
(`None` or empty string), the total number of records and the completeness
ratio:

```text
completeness = (total - missing) / total
```

## 4. Freshness and SLA

The report compares the latest `snapshot_timestamp` with the current time. The
default SLA is **15 minutes** (three pipeline intervals of five minutes).

```json
{
  "latest_snapshot": "2026-10-19T20:25:55+00:00",
  "age_minutes": 4.2,
  "sla_minutes": 15,
  "is_fresh": true
}
```

A stale dataset sets `is_fresh` to `false` and therefore fails the quality gate.


## 5. Metrics output

`python -m governance.quality_metrics` writes to
`data/gold/quality_metrics/`:

| File | Content |
|---|---|
| `quality_metrics_<timestamp>.json` | Full report for one run (history). |
| `latest.json` | Full report of the latest run. |
| `quality_summary.parquet` | One row with record count, issues, freshness and gate status. |
| `column_completeness.parquet` | One row per column with missing count and ratio. |
| `rule_issues.parquet` | One row per rule with the detected count. |

The same files are uploaded to
`s3://<bucket>/gold/bicimad/quality_metrics/` by the pipeline.

## 6. Quality gate

`build_quality_metrics()` returns `passed: true` only when:

- there are no rule issues,
- there are no missing or unexpected columns,
- there are no type mismatches,
- the dataset is fresh according to the SLA.

The pipeline logs the result and stops on rule issues.

## 7. Commands

```bash
# Run only the metrics report.
python -m governance.quality_metrics

# Run the rule-based report.
python -m etl.bicimad_quality_report

# Run all automated tests.
python -m pytest -v

# Check code quality.
python -m ruff check .
```

## 8. Continuous integration

GitHub Actions runs Ruff and the full pytest suite on every push and pull
request targeting `main`. The new tests cover schema validation, completeness,
freshness and the JSON/Parquet output of the quality report.

## 9. Querying the metrics

The Parquet tables can be registered in the Glue Data Catalog and queried with
Athena. See `docs/athena_queries.md` for examples, including how to find the
columns with the lowest completeness and the latest gate status.
