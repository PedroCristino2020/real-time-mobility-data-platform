import time

from .bicimad_ingestion import main


INTERVAL_SECONDS = 5 * 60


def run():
    while True:
        print("Starting BiciMAD ingestion...")

        try:
            main()
            print("Ingestion completed successfully.")
        except Exception as error:
            print(f"Ingestion failed: {error}")

        print(f"Waiting {INTERVAL_SECONDS} seconds...")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run()