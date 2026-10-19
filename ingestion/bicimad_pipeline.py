
import logging
import time

from etl.bicimad_quality_report import main as run_quality_report
from etl.bicimad_status_transform import main as transform_status
from etl.bicimad_to_parquet import main as convert_to_parquet
from etl.bicimad_transform import main as transform_stations
from etl.s3_silver_upload import (
    upload_silver_json,
    upload_silver_parquet,
)
from ingestion.bicimad_ingestion import main as ingest
from spark.bicimad_processing import main as process_gold
from spark.s3_gold_upload import main as upload_gold

logger = logging.getLogger(__name__)

INTERVAL_SECONDS = 5 * 60

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def run_once():
    logger.info("=== 1. Ingestion and Raw upload ===")
    ingest()

    logger.info("=== 2. Transform station information ===")
    transform_stations()

    logger.info("=== 3. Transform station status ===")
    transform_status()

    logger.info("=== 4. Data quality ===")
    total_issues = run_quality_report()

    if total_issues is None:
        raise RuntimeError(
            "The quality report did not return an issue count."
        )

    if total_issues > 0:
        raise RuntimeError(
            f"Pipeline stopped: {total_issues} data quality issues found."
        )

    logger.info("=== 5. Convert Silver data to Parquet ===")
    convert_to_parquet()

    logger.info("=== 6. Upload Silver datasets ===")
    upload_silver_json()
    upload_silver_parquet()

    logger.info("=== 7. Generate Gold dataset with Spark ===")
    process_gold()

    logger.info("=== 8. Upload Gold dataset ===")
    upload_gold()

    logger.info("Pipeline completed successfully.")


def run_forever():
    logger.info(
        "Starting BiciMAD pipeline. Interval: %s seconds.",
        INTERVAL_SECONDS,
    )

    while True:
        try:
            run_once()
        except Exception:
            logger.exception("Pipeline execution failed.")

        logger.info(
            "Waiting %s seconds until next run.",
            INTERVAL_SECONDS,
        )
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run_forever()
