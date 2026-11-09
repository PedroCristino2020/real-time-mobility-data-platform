
from pathlib import Path

from ingestion.s3_storage import upload_file

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUALITY_DIR = PROJECT_ROOT / "data" / "gold" / "quality_metrics"


def main():
    if not QUALITY_DIR.is_dir():
        raise FileNotFoundError(
            f"Quality metrics not found: {QUALITY_DIR}. "
            "Run governance.quality_metrics first."
        )

    files = sorted(
        path for path in QUALITY_DIR.iterdir() if path.is_file()
    )

    if not files:
        raise FileNotFoundError(
            f"No quality metric files found in {QUALITY_DIR}"
        )

    for local_path in files:
        object_key = f"gold/bicimad/quality_metrics/{local_path.name}"
        upload_file(local_path, object_key)

    print(
        f"Quality metrics uploaded successfully: "
        f"{len(files)} file(s)."
    )


if __name__ == "__main__":
    main()
