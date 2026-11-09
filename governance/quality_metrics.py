from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from etl.bicimad_data_quality import VALID_STATUS_VALUES, validate_records

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "silver" / "bicimad" / "station_status.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "gold" / "quality_metrics"

DATASET = "silver_station_status"
SCHEMA_VERSION = "1.0"
FRESHNESS_SLA_MINUTES = 15

# Expected logical types for every Silver column. ``timestamp`` values are
# stored as ISO-8601 strings in the Silver JSON dataset.
EXPECTED_SCHEMA = {
    "snapshot_timestamp": "timestamp",
    "station_id": "string",
    "num_bikes_available": "integer",
    "num_bikes_disabled": "integer",
    "num_docks_available": "integer",
    "num_docks_disabled": "integer",
    "status": "string",
    "is_renting": "boolean",
    "is_returning": "boolean",
    "last_reported": "integer",
}


def parse_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _matches_type(value, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "timestamp":
        return parse_timestamp(value) is not None
    return False


def validate_schema(records: list[dict]) -> dict:
    if not records:
        return {
            "missing_columns": sorted(EXPECTED_SCHEMA),
            "unexpected_columns": [],
            "type_mismatches": {},
        }

    columns = {column for record in records for column in record}

    mismatches = {}
    for column, expected_type in EXPECTED_SCHEMA.items():
        invalid = sum(
            1
            for record in records
            if record.get(column) is not None
            and not _matches_type(record.get(column), expected_type)
        )
        if invalid:
            mismatches[column] = invalid

    return {
        "missing_columns": sorted(set(EXPECTED_SCHEMA) - columns),
        "unexpected_columns": sorted(columns - set(EXPECTED_SCHEMA)),
        "type_mismatches": mismatches,
    }


def compute_completeness(records: list[dict]) -> dict:
    total = len(records)
    completeness = {}

    for column in EXPECTED_SCHEMA:
        missing = sum(
            1 for record in records if record.get(column) in (None, "")
        )
        ratio = round((total - missing) / total, 4) if total else 0.0
        completeness[column] = {
            "missing": missing,
            "total": total,
            "completeness": ratio,
        }

    return completeness


def compute_freshness(
    records: list[dict],
    now: datetime | None = None,
    sla_minutes: int = FRESHNESS_SLA_MINUTES,
) -> dict:
    timestamps = [
        parsed
        for parsed in (
            parse_timestamp(record.get("snapshot_timestamp"))
            for record in records
        )
        if parsed is not None
    ]

    if not timestamps:
        return {
            "latest_snapshot": None,
            "age_minutes": None,
            "sla_minutes": sla_minutes,
            "is_fresh": False,
        }

    latest = max(timestamps)
    reference = now or datetime.now(UTC)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)

    age_minutes = round((reference - latest).total_seconds() / 60, 2)

    return {
        "latest_snapshot": latest.isoformat(),
        "age_minutes": age_minutes,
        "sla_minutes": sla_minutes,
        "is_fresh": age_minutes <= sla_minutes,
    }


def build_quality_metrics(
    records: list[dict],
    dataset: str = DATASET,
    now: datetime | None = None,
) -> dict:
    reference = now or datetime.now(UTC)
    rule_issues = validate_records(records)
    schema = validate_schema(records)
    freshness = compute_freshness(records, now=reference)
    total_rule_issues = sum(rule_issues.values())

    schema_ok = (
        not schema["missing_columns"]
        and not schema["unexpected_columns"]
        and not schema["type_mismatches"]
    )

    return {
        "dataset": dataset,
        "generated_at": reference.isoformat(),
        "record_count": len(records),
        "schema_version": SCHEMA_VERSION,
        "expected_status_values": sorted(VALID_STATUS_VALUES),
        "schema_validation": schema,
        "completeness": compute_completeness(records),
        "freshness": freshness,
        "rule_issues": rule_issues,
        "total_rule_issues": total_rule_issues,
        "passed": schema_ok and freshness["is_fresh"] and total_rule_issues == 0,
    }


def write_quality_metrics(metrics: dict, output_dir: Path = OUTPUT_DIR) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reference = parse_timestamp(metrics["generated_at"])
    stamp = reference.strftime("%Y%m%dT%H%M%SZ") if reference else "unknown"

    history_path = output_dir / f"quality_metrics_{stamp}.json"
    with open(history_path, "w", encoding="utf-8") as file:
        json.dump(metrics, file, ensure_ascii=False, indent=2)

    latest_path = output_dir / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as file:
        json.dump(metrics, file, ensure_ascii=False, indent=2)

    schema = metrics["schema_validation"]
    summary = pd.DataFrame(
        [
            {
                "generated_at": metrics["generated_at"],
                "dataset": metrics["dataset"],
                "record_count": metrics["record_count"],
                "total_rule_issues": metrics["total_rule_issues"],
                "missing_columns": len(schema["missing_columns"]),
                "unexpected_columns": len(schema["unexpected_columns"]),
                "type_mismatches": sum(schema["type_mismatches"].values()),
                "freshness_age_minutes": metrics["freshness"]["age_minutes"],
                "freshness_sla_minutes": metrics["freshness"]["sla_minutes"],
                "is_fresh": metrics["freshness"]["is_fresh"],
                "passed": metrics["passed"],
            }
        ]
    )
    summary_path = output_dir / "quality_summary.parquet"
    summary.to_parquet(summary_path, index=False)

    completeness = pd.DataFrame(
        [
            {
                "generated_at": metrics["generated_at"],
                "dataset": metrics["dataset"],
                "column": column,
                "missing": values["missing"],
                "total": values["total"],
                "completeness": values["completeness"],
            }
            for column, values in metrics["completeness"].items()
        ]
    )
    completeness_path = output_dir / "column_completeness.parquet"
    completeness.to_parquet(completeness_path, index=False)

    rule_issues = pd.DataFrame(
        [
            {
                "generated_at": metrics["generated_at"],
                "rule": rule,
                "count": count,
            }
            for rule, count in metrics["rule_issues"].items()
        ]
    )
    rule_issues_path = output_dir / "rule_issues.parquet"
    rule_issues.to_parquet(rule_issues_path, index=False)

    return {
        "history": history_path,
        "latest": latest_path,
        "summary": summary_path,
        "completeness": completeness_path,
        "rule_issues": rule_issues_path,
    }


def load_records(input_file: Path = INPUT_FILE) -> list[dict]:
    with open(input_file, encoding="utf-8") as file:
        return json.load(file)


def run(
    input_file: Path = INPUT_FILE,
    output_dir: Path = OUTPUT_DIR,
    now: datetime | None = None,
) -> dict:
    records = load_records(input_file)
    metrics = build_quality_metrics(records, now=now)
    write_quality_metrics(metrics, output_dir)
    return metrics


def main() -> int:
    metrics = run()

    print(f"Dataset: {metrics['dataset']}")
    print(f"Records: {metrics['record_count']}")
    print(f"Schema version: {metrics['schema_version']}")
    print(
        "Schema validation: "
        f"{len(metrics['schema_validation']['missing_columns'])} missing columns, "
        f"{len(metrics['schema_validation']['unexpected_columns'])} unexpected columns, "
        f"{sum(metrics['schema_validation']['type_mismatches'].values())} type mismatches"
    )
    print(
        "Freshness: "
        f"{metrics['freshness']['age_minutes']} min "
        f"(SLA {metrics['freshness']['sla_minutes']} min, "
        f"fresh={metrics['freshness']['is_fresh']})"
    )

    print("\nRule issues:")
    for rule, count in metrics["rule_issues"].items():
        print(f"  {rule}: {count}")

    print(f"\nTotal rule issues: {metrics['total_rule_issues']}")
    print(f"Quality gate passed: {metrics['passed']}")
    print(f"Metrics written to: {OUTPUT_DIR}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
