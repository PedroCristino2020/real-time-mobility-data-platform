from datetime import datetime, timezone
import json
import os

import requests


BASE_URL = "https://madrid.publicbikesystem.net/customer/gbfs/v2/es"

FEEDS = {
    "station_information": f"{BASE_URL}/station_information", #La f es para meter variables
    "station_status": f"{BASE_URL}/station_status",
}

OUTPUT_DIR = "data/raw/bicimad"


def fetch_json(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def save_json(data, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print(f"Saved: {output_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

    # Station information: download only if it does not exist
    
    station_information_path = os.path.join(OUTPUT_DIR, "station_information.json")

    if os.path.exists(station_information_path):
        print("station_information already exists. Skipping download.")
    else:
        print("Downloading station_information...")
        data = fetch_json(FEEDS["station_information"])
        save_json(data, station_information_path)

    # Station status: download every time
    print("Downloading station_status...")

    data = fetch_json(FEEDS["station_status"])

    status_dir = os.path.join(OUTPUT_DIR, "station_status")

    os.makedirs(status_dir, exist_ok=True)

    output_path = os.path.join(status_dir,f"{timestamp}.json")
    save_json(data, output_path)


if __name__ == "__main__":
    main()