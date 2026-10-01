import json

INPUT_FILE = "data/silver/bicimad/station_status.json"

VALID_STATUS_VALUES = { "IN_SERVICE", "NOT_IN_SERVICE",}

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        records = json.load(file)

    print(f"Total records: {len(records)}")

    missing_station_ids = 0
    duplicate_station_snapshots = 0
    negative_bikes = 0
    negative_docks = 0
    invalid_status_values = 0
    missing_timestamps = 0

    station_snapshot_keys = set()

    for record in records:
        station_id = record.get("station_id")
        snapshot_timestamp = record.get("snapshot_timestamp")

        if not station_id:
            missing_station_ids += 1
        else:
            key = (snapshot_timestamp, station_id)

            if key in station_snapshot_keys:
                duplicate_station_snapshots += 1

        station_snapshot_keys.add(key)

        if record["num_bikes_available"] < 0:
            negative_bikes += 1

        if record["num_docks_available"] < 0:
            negative_docks += 1

        if record["status"] not in VALID_STATUS_VALUES:
            invalid_status_values += 1

        if not record["snapshot_timestamp"]:
            missing_timestamps += 1
    
    print(f"Missing station IDs: {missing_station_ids}")
    print(f"Duplicate station IDs: {duplicate_station_snapshots}")
    print(f"Negative bike values: {negative_bikes}")
    print(f"Negative dock values: {negative_docks}")
    print(f"Invalid status values: {invalid_status_values}")
    print(f"Missing timestamps: {missing_timestamps}")

if __name__ == "__main__":
    main()  