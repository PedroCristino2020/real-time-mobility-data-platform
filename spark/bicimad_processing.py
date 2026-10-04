from pyspark.sql import SparkSession

INPUT_FILE = "data/silver/bicimad/station_status"

def main():
    spark = SparkSession.builder.appName("BicimadProcessing").getOrCreate()

    spark.conf.set("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem")

    spark.conf.set("spark.hadoop.fs.file.impl.disable.cache", "true")

    df = spark.read.parquet(INPUT_FILE)

    print(f"Number of rows: {df.count()}")
    print(f"Number of columns: {len(df.columns)}")

    df.printSchema()
    df.show(5)

    spark.stop()

if __name__ == "__main__":
    main()