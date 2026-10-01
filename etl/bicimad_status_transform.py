import json
import glob
import os
from datetime import datetime

INPUT_PATTERN = "data/raw/bicimad/station_status/*.json"
OUTPUT_FILE = "data/silver/bicimad/station_status.json"

def main():
    files = glob.glob(INPUT_PATTERN)

    print(f"Snapshots found: {len(files)}")

    status = []

    for file_path in files:
        filename = os.path.basename(file_path)
        
        timestamp_text = filename.replace(".json", "")
        snapshot_timestamp = datetime.strptime(timestamp_text, "%Y-%m-%d_%H-%M-%S")


        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        stations = data["data"]["stations"]

        for station in stations:
            status.append({
                "snapshot_timestamp": snapshot_timestamp.isoformat(),
                "station_id": station["station_id"],
                "num_bikes_available": station["num_bikes_available"],
                "num_bikes_disabled": station["num_bikes_disabled"],
                "num_docks_available": station["num_docks_available"],
                "num_docks_disabled": station["num_docks_disabled"],
                "status": station["status"],
                "is_renting": station["is_renting"],
                "is_returning": station["is_returning"],
                "last_reported": station["last_reported"],
            })

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(status, file, ensure_ascii=False, indent=2)

    print(f"Records generated: {len(status)}")
    print(f"Saved: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()