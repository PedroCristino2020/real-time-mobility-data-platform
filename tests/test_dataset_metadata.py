import pandas as pd

from governance.dataset_metadata import build_manifest, describe_path


def test_describe_missing_path(tmp_path):
    info = describe_path(tmp_path / "missing", "parquet")

    assert info["exists"] is False
    assert info["row_count"] == 0
    assert info["columns"] == []


def test_describe_parquet_dataset(tmp_path):
    partition = tmp_path / "dataset" / "date=2026-10-01"
    partition.mkdir(parents=True)
    pd.DataFrame({"station_id": ["1", "2"]}).to_parquet(
        partition / "part.parquet", index=False
    )

    info = describe_path(tmp_path / "dataset", "parquet")

    assert info["exists"] is True
    assert info["row_count"] == 2
    assert info["columns"] == ["station_id"]
    assert info["partitions"] == ["date=2026-10-01"]


def test_build_manifest_contains_governance_fields(tmp_path):
    config = {
        "bucket": "test-bucket",
        "owner": "Test Owner",
        "naming": {"partition_pattern": "date=YYYY-MM-DD"},
        "tags": {"project": "test"},
    }
    definition = {
        "name": "silver_station_status",
        "layer": "silver",
        "path": "data/silver/bicimad/station_status",
        "format": "parquet",
        "record_unit": "rows",
        "source": "test source",
        "schema_version": "1.0",
        "freshness_sla_minutes": 15,
        "partition_columns": ["date"],
        "tags": {"update_frequency": "5-minutes"},
    }

    manifest = build_manifest(definition, config, root=tmp_path)

    assert manifest["dataset"] == "silver_station_status"
    assert manifest["location"]["s3_uri"] == (
        "s3://test-bucket/silver/bicimad/station_status"
    )
    assert manifest["tags"]["project"] == "test"
    assert manifest["tags"]["update_frequency"] == "5-minutes"
    assert manifest["partition_columns"] == ["date"]
    assert manifest["schema_version"] == "1.0"
