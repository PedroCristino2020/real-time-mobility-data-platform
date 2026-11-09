from __future__ import annotations

from pathlib import Path

from pyspark.sql import SparkSession

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE = PROJECT_ROOT / "data" / "iceberg_warehouse"
SILVER_STATUS = PROJECT_ROOT / "data" / "silver" / "bicimad" / "station_status"

ICEBERG_VERSION = "1.11.0"
SPARK_MINOR = "4.1"


def _as_uri(path: Path) -> str:
    return path.resolve().as_uri()


def build_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("BicimadIcebergLocal")
        .master("local[*]")
        .config(
            "spark.jars.packages",
            "org.apache.iceberg:"
            f"iceberg-spark-runtime-{SPARK_MINOR}_2.13:{ICEBERG_VERSION}",
        )
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .config(
            "spark.sql.catalog.local",
            "org.apache.iceberg.spark.SparkCatalog",
        )
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", _as_uri(WAREHOUSE))
        .getOrCreate()
    )


def main() -> None:
    WAREHOUSE.mkdir(parents=True, exist_ok=True)
    spark = build_spark()

    spark.sql("CREATE DATABASE IF NOT EXISTS local.bicimad")

    silver = spark.read.parquet(_as_uri(SILVER_STATUS))
    silver.createOrReplaceTempView("silver_station_status")

    spark.sql(
        """
        CREATE OR REPLACE TABLE local.bicimad.station_status
        USING iceberg
        PARTITIONED BY (days(snapshot_timestamp))
        TBLPROPERTIES ('write.target-file-size-bytes' = '134217728')
        AS SELECT * FROM silver_station_status
        """
    )

    print("Iceberg table created at:", _as_uri(WAREHOUSE / "bicimad.db" / "station_status"))

    spark.sql(
        """
        SELECT station_id, ROUND(AVG(num_bikes_available), 2) AS avg_bikes
        FROM local.bicimad.station_status
        GROUP BY station_id
        ORDER BY avg_bikes DESC
        LIMIT 10
        """
    ).show(truncate=False)

    print("Snapshots:")
    spark.sql(
        """
        SELECT snapshot_id, committed_at, operation
        FROM local.bicimad.station_status.snapshots
        """
    ).show(truncate=False)

    print("Partitions:")
    spark.sql(
        """
        SELECT partition, record_count, file_count
        FROM local.bicimad.station_status.partitions
        """
    ).show(truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()
