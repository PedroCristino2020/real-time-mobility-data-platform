from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "datasets.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "_metadata"


def load_config(config_file: Path = CONFIG_FILE) -> dict:
    with open(config_file, encoding="utf-8") as file:
        return json.load(file)


def _s3_prefix(local_path: str) -> str:
    return local_path.replace("\\", "/").removeprefix("data/")


def _parquet_metadata(file: Path):
    try:
        return pq.ParquetFile(file)
    except (OSError, ValueError, pa.ArrowException):
        return None


def _parquet_columns(files: list[Path]) -> list[str]:
    for file in files:
        if file.suffix == ".parquet":
            parquet = _parquet_metadata(file)
            if parquet is not None:
                return list(parquet.schema_arrow.names)
    return []


def _json_columns(path: Path) -> list[str]:
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []

    if isinstance(data, list):
        return sorted({key for record in data for key in record})
    if isinstance(data, dict):
        stations = data.get("data", {}).get("stations")
        if isinstance(stations, list) and stations:
            return sorted({key for record in stations for key in record})
        return sorted(data.keys())
    return []


def _parquet_rows(files: list[Path]) -> int:
    total = 0
    for file in files:
        if file.suffix == ".parquet":
            parquet = _parquet_metadata(file)
            if parquet is not None:
                total += parquet.metadata.num_rows
    return total


def _json_rows(path: Path) -> int:
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return 0
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        stations = data.get("data", {}).get("stations")
        if isinstance(stations, list):
            return len(stations)
        return 1
    return 0


def describe_path(path: Path, data_format: str, record_unit: str = "rows",) -> dict:
    if not path.exists():
        return {
            "exists": False,
            "size_bytes": 0,
            "row_count": 0,
            "columns": [],
            "partitions": [],
            "file_count": 0,
        }

    files = [item for item in path.rglob("*") if item.is_file()] if path.is_dir() else [path]
    size_bytes = sum(item.stat().st_size for item in files)
    partitions = sorted(
        {
            item.parent.name
            for item in files
            if item.parent.name.startswith("date=")
        }
    )

    if data_format == "parquet":
        columns = _parquet_columns(files)
        row_count = _parquet_rows(files)
    elif data_format == "json" and not path.is_dir():
        columns = _json_columns(path)
        row_count = _json_rows(path)
    else:
        columns = []
        if data_format == "json":
            json_files = sorted(item for item in files if item.suffix == ".json")
            if json_files:
                columns = _json_columns(json_files[0])
        row_count = len(files) if record_unit == "files" else 0

    return {
        "exists": True,
        "size_bytes": size_bytes,
        "row_count": row_count,
        "columns": columns,
        "partitions": partitions,
        "file_count": len(files),
    }


def build_manifest(definition: dict, config: dict, root: Path = PROJECT_ROOT) -> dict:
    local_path = definition["path"]
    path = root / local_path
    info = describe_path(
        path,
        definition.get("format", "parquet"),
        definition.get("record_unit", "rows"),
    )

    tags = dict(config.get("tags", {}))
    tags.update(definition.get("tags", {}))

    return {
        "dataset": definition["name"],
        "layer": definition["layer"],
        "format": definition["format"],
        "location": {
            "local_path": local_path,
            "s3_uri": f"s3://{config['bucket']}/{_s3_prefix(local_path)}",
        },
        "source": definition["source"],
        "owner": config["owner"],
        "schema_version": definition["schema_version"],
        "freshness_sla_minutes": definition["freshness_sla_minutes"],
        "partition_columns": definition.get("partition_columns", []),
        "partition_pattern": config["naming"]["partition_pattern"],
        "tags": tags,
        "generated_at": datetime.now(UTC).isoformat(),
        **info,
    }


def build_catalog(config: dict | None = None, root: Path = PROJECT_ROOT) -> dict:
    config = config or load_config()
    manifests = [
        build_manifest(definition, config, root)
        for definition in config["datasets"]
    ]
    return {
        "project": config["project"],
        "owner": config["owner"],
        "bucket": config["bucket"],
        "naming": config["naming"],
        "generated_at": datetime.now(UTC).isoformat(),
        "datasets": manifests,
    }


def write_manifests(catalog: dict, output_dir: Path = OUTPUT_DIR) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []

    for manifest in catalog["datasets"]:
        path = output_dir / f"{manifest['dataset']}.json"
        with open(path, "w", encoding="utf-8") as file:
            json.dump(manifest, file, ensure_ascii=False, indent=2)
        written.append(path)

    catalog_path = output_dir / "catalog.json"
    with open(catalog_path, "w", encoding="utf-8") as file:
        json.dump(catalog, file, ensure_ascii=False, indent=2)
    written.append(catalog_path)

    return written


def upload_manifests(output_dir: Path = OUTPUT_DIR) -> None:
    from ingestion.s3_storage import upload_file

    for path in sorted(output_dir.glob("*.json")):
        upload_file(path, f"_metadata/{path.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload the generated manifests to the S3-compatible storage.",
    )
    args = parser.parse_args()

    catalog = build_catalog()
    written = write_manifests(catalog)

    for manifest in catalog["datasets"]:
        state = "ok" if manifest["exists"] else "missing"
        print(
            f"{manifest['dataset']}: {state}, "
            f"{manifest['row_count']} records, "
            f"{len(manifest['columns'])} columns, "
            f"{len(manifest['partitions'])} partitions"
        )

    print(f"\nManifests written: {len(written)} files under {OUTPUT_DIR}")

    if args.upload:
        upload_manifests()
        print("Manifests uploaded to the S3-compatible storage.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
