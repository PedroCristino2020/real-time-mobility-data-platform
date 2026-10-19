
from pathlib import Path

from ingestion.s3_storage import upload_file

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver" / "bicimad"


def upload_silver_json():
    """Upload the Silver JSON datasets to Silo."""
    files = [
        (
            SILVER_DIR / "stations.json",
            "silver/bicimad/stations.json",
        ),
        (
            SILVER_DIR / "station_status.json",
            "silver/bicimad/station_status.json",
        ),
    ]

    for local_path, object_key in files:
        if not local_path.is_file():
            raise FileNotFoundError(
                f"Silver file not found: {local_path}. "
                "Run its transformation first."
            )

        upload_file(local_path, object_key)


def upload_silver_parquet():
    """Upload all date-partitioned Silver Parquet files to Silo."""
    parquet_files = sorted(SILVER_DIR.glob("station_status/date=*/*.parquet"))

    if not parquet_files:
        raise FileNotFoundError(
            f"No Parquet files found under {SILVER_DIR / 'station_status'}"
        )

    for local_path in parquet_files:
        relative_path = local_path.relative_to(SILVER_DIR).as_posix()
        object_key = f"silver/bicimad/{relative_path}"
        upload_file(local_path, object_key)


if __name__ == "__main__":
    upload_silver_json()
    upload_silver_parquet()
    print("Silver datasets uploaded successfully.")
