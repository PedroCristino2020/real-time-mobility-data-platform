"""Run the local DuckDB validation queries against the project datasets.

The SQL in ``sql/duckdb`` mirrors the Athena queries documented in
``docs/athena_queries.md`` but uses ``read_parquet`` so it can run for free
against the local files. No AWS account or paid service is required.

Usage:
    python -m governance.run_local_queries
    python -m governance.run_local_queries --file sql/duckdb/station_queries.sql
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUERY_DIR = PROJECT_ROOT / "sql" / "duckdb"


def split_statements(sql: str) -> list[str]:
    """Split a SQL file into executable statements."""
    return [
        statement.strip()
        for statement in sql.split(";")
        if statement.strip()
    ]


def run_file(path: Path, project_root: Path = PROJECT_ROOT) -> list:
    """Execute every statement in a SQL file and return the result frames."""
    previous_dir = Path.cwd()
    os.chdir(project_root)

    try:
        connection = duckdb.connect()
        results = []

        for statement in split_statements(path.read_text(encoding="utf-8")):
            results.append(connection.execute(statement).fetchdf())

        connection.close()
    finally:
        os.chdir(previous_dir)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file",
        type=Path,
        default=QUERY_DIR / "station_queries.sql",
        help="SQL file to execute.",
    )
    args = parser.parse_args()

    path = args.file
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    print(f"Running local DuckDB queries: {path}\n")

    for index, result in enumerate(run_file(path), start=1):
        print(f"--- Result {index} ---")
        print(result.to_string(index=False))
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
