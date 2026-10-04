from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, count, col, round
import os

INPUT_FILE = "data/silver/bicimad/station_status"

def main():
    spark = SparkSession.builder.appName("BicimadProcessing").getOrCreate()

    df = spark.read.parquet(INPUT_FILE)

    print(f"Number of rows: {df.count()}")
    print(f"Number of columns: {len(df.columns)}")

    df.printSchema()

    stations_df = spark.read.option("multiLine", True).json("data/silver/bicimad/stations.json")
    stations_df.printSchema()

    station_metrics = (
        df.groupBy("station_id").agg(
            avg("num_bikes_available").alias("avg_bikes_available"),
            avg("num_docks_available").alias("avg_docks_available"),
            count("*").alias("snapshot_count")
        )
    )

    station_metrics = station_metrics.withColumn(
        "availability_rate", col("avg_bikes_available") / (col("avg_bikes_available") + col("avg_docks_available"))
    )

    station_metrics = station_metrics.join(stations_df.select("station_id", "name", "capacity"), on="station_id", how="left")

    station_metrics = station_metrics.withColumn("availability_percentage", round(col("availability_rate") * 100, 2))

    station_metrics = station_metrics.orderBy(col("availability_rate").desc())

    station_metrics.show(10, truncate=False)

    OUTPUT_FILE = "data/gold/bicimad/station_availability_spark"

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    station_metrics.write.mode("overwrite").parquet(OUTPUT_FILE)

    print(f"Gold dataset saved to: {OUTPUT_FILE}")

    gold_df = spark.read.parquet(OUTPUT_FILE)
    print(f"Gold rows: {gold_df.count()}")
    print(f"Gold columns: {gold_df.columns}")

    print("Null station IDs:")
    print(gold_df.filter(col("station_id").isNull()).count())

    print("Invalid availability percentages:")
    print(gold_df.filter((col("availability_percentage") < 0) | (col("availability_percentage") > 100)).count())

    spark.stop()

if __name__ == "__main__":
    main()