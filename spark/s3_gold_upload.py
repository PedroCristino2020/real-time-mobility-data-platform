
from pathlib import Path

from ingestion.s3_storage import upload_file

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = PROJECT_ROOT / "data" / "gold" / "bicimad"
GOLD_DATASET = GOLD_DIR / "station_availability_spark"


def main():
    if not GOLD_DATASET.is_dir():
        raise FileNotFoundError(
            f"Gold dataset not found: {GOLD_DATASET}. "
            "Run the Spark processing first."
        )

    parquet_files = sorted(GOLD_DATASET.rglob("*.parquet"))

    if not parquet_files:
        raise FileNotFoundError(
            f"No Parquet files found in {GOLD_DATASET}"
        )

    for local_path in parquet_files:
        relative_path = local_path.relative_to(GOLD_DIR).as_posix()
        object_key = f"gold/bicimad/{relative_path}"

        upload_file(local_path, object_key)

    print(
        f"Gold dataset uploaded successfully: "
        f"{len(parquet_files)} Parquet file(s)."
    )


if __name__ == "__main__":
    main()
