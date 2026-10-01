import json

FILES = [
    "data/raw/bicimad/station_information.json",
    "data/raw/bicimad/station_status.json"
]

for file_path in FILES:
    print(f"\n{'=' * 60}")
    print(f"FILE: {file_path}")
    print(f"{'=' * 60}")

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    print("\nTop-level keys:")
    print(data.keys())

    print("\nData keys:")
    print(data["data"].keys())

    stations = data["data"]["stations"]

    print("\nNumber of stations:")
    print(len(stations))

    print("\nFirst station:")
    print(stations[0])

    print("\nFields in first station:")
    print(stations[0].keys())