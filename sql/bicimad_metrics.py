import os

import pandas as pd

STATUS_FILE = "data/silver/bicimad/station_status"
STATIONS_FILE = "data/silver/bicimad/stations.json"
OUTPUT_FILE = "data/gold/bicimad/station_availability.parquet"

def main():
    status_df = pd.read_parquet(STATUS_FILE)
    stations_df = pd.read_json(STATIONS_FILE)

    status_df["station_id"] = status_df["station_id"].astype(str)
    stations_df["station_id"] = stations_df["station_id"].astype(str)

    df = status_df.merge(stations_df[["station_id", "name","capacity"]], on="station_id", how="left")

    df["availability_rate"] = df["num_bikes_available"] / df["capacity"]

    station_metrics = (df.groupby(["station_id", "name", "capacity"])["availability_rate"].mean().reset_index())

    station_metrics["availability_percentage"] = (station_metrics["availability_rate"] * 100).round(2)

    station_metrics = station_metrics.sort_values("availability_rate")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    station_metrics.to_parquet(OUTPUT_FILE, engine="pyarrow", index=False)

    print(station_metrics.head(10))
    print(f"\nSaved: {OUTPUT_FILE}")

if __name__ == "__main__":
    main() 