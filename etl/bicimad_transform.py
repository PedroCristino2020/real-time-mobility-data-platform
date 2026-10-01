import json
import os

INPUT_FILE = "data/raw/bicimad/station_information.json"

OUTPUT_FILE = "data/silver/bicimad/stations.json"


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    stations = data["data"]["stations"]

    selected_stations = []

    for station in stations:
        selected_station = {
            "station_id": station["station_id"],
            "name": station["name"],
            "lat": station["lat"],
            "lon": station["lon"],
            "address": station["address"],
            "capacity": station["capacity"],
            "is_charging_station": station["is_charging_station"],
            "is_virtual_station": station["is_virtual_station"],
        }
        selected_stations.append(selected_station)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(selected_stations, file, ensure_ascii=False, indent=2)

    print(f"Saved: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()