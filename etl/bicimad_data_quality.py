VALID_STATUS_VALUES = {"IN_SERVICE", "NOT_IN_SERVICE"}


def validate_records(records):
    """Validate BiciMAD station status records and return error counts."""

    issues = {
        "missing_station_ids": 0,
        "duplicate_station_snapshots": 0,
        "negative_bikes": 0,
        "negative_docks": 0,
        "invalid_status_values": 0,
        "missing_timestamps": 0,
        "missing_numeric_values": 0,
    }

    station_snapshot_keys = set()

    for record in records:
        station_id = record.get("station_id")
        snapshot_timestamp = record.get("snapshot_timestamp")

        if station_id is None or station_id == "":
            issues["missing_station_ids"] += 1
        elif snapshot_timestamp:
            key = (snapshot_timestamp, station_id)

            if key in station_snapshot_keys:
                issues["duplicate_station_snapshots"] += 1

            station_snapshot_keys.add(key)

        if not snapshot_timestamp:
            issues["missing_timestamps"] += 1

        bikes = record.get("num_bikes_available")
        docks = record.get("num_docks_available")

        if bikes is None:
            issues["missing_numeric_values"] += 1
        elif bikes < 0:
            issues["negative_bikes"] += 1

        if docks is None:
            issues["missing_numeric_values"] += 1
        elif docks < 0:
            issues["negative_docks"] += 1

        if record.get("status") not in VALID_STATUS_VALUES:
            issues["invalid_status_values"] += 1

    return issues