from datetime import UTC, datetime

import pandas as pd

from governance.quality_metrics import (
    EXPECTED_SCHEMA,
    build_quality_metrics,
    compute_completeness,
    compute_freshness,
    validate_schema,
    write_quality_metrics,
)


def make_record(**overrides):
    record = {
        "snapshot_timestamp": "2026-10-15T10:00:00",
        "station_id": "1406",
        "num_bikes_available": 10,
        "num_bikes_disabled": 0,
        "num_docks_available": 20,
        "num_docks_disabled": 0,
        "status": "IN_SERVICE",
        "is_renting": True,
        "is_returning": True,
        "last_reported": 1790864007,
    }
    record.update(overrides)
    return record


def test_valid_record_passes_schema_and_rules():
    now = datetime(2026, 10, 15, 10, 5, tzinfo=UTC)

    metrics = build_quality_metrics([make_record()], now=now)

    assert metrics["schema_validation"]["missing_columns"] == []
    assert metrics["schema_validation"]["unexpected_columns"] == []
    assert metrics["schema_validation"]["type_mismatches"] == {}
    assert metrics["total_rule_issues"] == 0
    assert metrics["freshness"]["is_fresh"] is True
    assert metrics["passed"] is True


def test_missing_column_is_detected():
    record = make_record()
    del record["status"]

    schema = validate_schema([record])

    assert "status" in schema["missing_columns"]


def test_unexpected_column_is_detected():
    schema = validate_schema([make_record(extra_field="x")])

    assert "extra_field" in schema["unexpected_columns"]


def test_type_mismatch_is_detected():
    schema = validate_schema([make_record(num_bikes_available="10")])

    assert schema["type_mismatches"]["num_bikes_available"] == 1


def test_completeness_counts_missing_values():
    records = [make_record(), make_record(station_id=None)]

    completeness = compute_completeness(records)

    assert completeness["station_id"]["missing"] == 1
    assert completeness["station_id"]["completeness"] == 0.5
    assert completeness["num_bikes_available"]["completeness"] == 1.0


def test_freshness_detects_stale_data():
    now = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)

    freshness = compute_freshness(
        [make_record()], now=now, sla_minutes=15
    )

    assert freshness["is_fresh"] is False
    assert freshness["age_minutes"] == 120.0


def test_write_quality_metrics_creates_json_and_parquet(tmp_path):
    now = datetime(2026, 10, 15, 10, 5, tzinfo=UTC)
    metrics = build_quality_metrics([make_record()], now=now)

    paths = write_quality_metrics(metrics, output_dir=tmp_path)

    for key in ["history", "latest", "summary", "completeness", "rule_issues"]:
        assert paths[key].is_file()

    summary = pd.read_parquet(paths["summary"])
    assert summary.loc[0, "record_count"] == 1
    assert bool(summary.loc[0, "passed"]) is True

    completeness = pd.read_parquet(paths["completeness"])
    assert set(completeness["column"]) == set(EXPECTED_SCHEMA)
