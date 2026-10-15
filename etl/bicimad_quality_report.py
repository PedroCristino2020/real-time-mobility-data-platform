import json

from etl.bicimad_data_quality import validate_records

INPUT_FILE = "data/silver/bicimad/station_status.json"


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        records = json.load(file)

    issues = validate_records(records)

    print(f"Total records: {len(records)}")
    print("\nData quality report:")

    for issue, count in issues.items():
        print(f"{issue}: {count}")

    total_issues = sum(issues.values())
    print(f"\nTotal detected issues: {total_issues}")


if __name__ == "__main__":
    main()