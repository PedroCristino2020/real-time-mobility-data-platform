import json
import os

import pandas as pd

INPUT_FILE = "data/silver/bicimad/stations.json"
OUTPUT_DIR = "data/silver/bicimad/stations"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "stations.parquet")


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    stations_df = pd.DataFrame(data)
    stations_df["station_id"] = stations_df["station_id"].astype(str)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    stations_df.to_parquet(OUTPUT_FILE, engine="pyarrow", index=False)

    print(f"Stations converted: {len(stations_df)}")
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Columns: {list(stations_df.columns)}")


if __name__ == "__main__":
    main()
