from etl.bicimad_data_quality import validate_records


def make_record(**overrides):
    record = {
        "station_id": "1406",
        "snapshot_timestamp": "2026-10-15T10:00:00",
        "num_bikes_available": 10,
        "num_docks_available": 20,
        "status": "IN_SERVICE",
    }
    record.update(overrides)
    return record


def test_valid_record_has_no_issues():
    issues = validate_records([make_record()])

    assert all(count == 0 for count in issues.values())


def test_missing_station_id_is_detected():
    issues = validate_records([make_record(station_id=None)])

    assert issues["missing_station_ids"] == 1


def test_duplicate_station_snapshot_is_detected():
    record = make_record()

    issues = validate_records([record, record.copy()])

    assert issues["duplicate_station_snapshots"] == 1


def test_negative_bikes_are_detected():
    issues = validate_records([make_record(num_bikes_available=-1)])

    assert issues["negative_bikes"] == 1


def test_negative_docks_are_detected():
    issues = validate_records([make_record(num_docks_available=-1)])

    assert issues["negative_docks"] == 1


def test_invalid_status_is_detected():
    issues = validate_records([make_record(status="UNKNOWN")])

    assert issues["invalid_status_values"] == 1


def test_missing_timestamp_is_detected():
    issues = validate_records([make_record(snapshot_timestamp=None)])

    assert issues["missing_timestamps"] == 1


def test_missing_numeric_values_are_detected():
    issues = validate_records([
        make_record(num_bikes_available=None, num_docks_available=None)
    ])

    assert issues["missing_numeric_values"] == 2