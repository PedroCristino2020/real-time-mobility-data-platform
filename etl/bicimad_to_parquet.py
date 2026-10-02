import json
import os

import pandas as pd

INPUT_FILE = "data/silver/bicimad/station_status.json"
OUTPUT_DIR = "data/silver/bicimad/station_status"

def main():
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    df["snapshot_timestamp"] = pd.to_datetime(df["snapshot_timestamp"], utc=True)

    df["date"] = df["snapshot_timestamp"].dt.strftime("%Y-%m-%d")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for date, partition in df.groupby("date"):
        partition_dir = os.path.join(OUTPUT_DIR, f"date={date}")

        os.makedirs(partition_dir, exist_ok=True)

        output_file = os.path.join(partition_dir, "station_status.parquet")

        partition = partition.drop(columns=["date"])

        partition.to_parquet(output_file, engine="pyarrow", index=False)

    print(f"Records converted: {len(df)}")
    print(f"Saved: {OUTPUT_DIR}")
    print(f"Columns: {list(df.columns)}")

if __name__ == "__main__":
    main()