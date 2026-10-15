# BiciMAD Data Platform Architecture

## Overview

The platform ingests real-world bike-sharing data from the BiciMAD GBFS API and processes it through Raw, Silver and Gold layers to produce station-level availability metrics.

## Architecture Diagram

```mermaid
flowchart TD
    A["BiciMAD GBFS API<br/>Station Information<br/>Station Status"]

    subgraph ING["Ingestion Layer"]
        B["Python Ingestion<br/>requests"]
    end

    subgraph RAW["Raw Layer"]
        C["Station Information<br/>JSON"]
        D["Timestamped Station Status<br/>JSON Snapshots"]
    end

    subgraph SILVER["Silver Layer"]
        E["Station Metadata<br/>Structured JSON"]
        F["Historical Station Status<br/>Structured JSON"]
        G["Data Quality Checks"]
        H["Date-Partitioned Parquet"]
    end

    subgraph GOLD["Gold Layer"]
        I["PySpark Processing"]
        J["Station Availability Metrics"]
    end

    K["Automated Tests<br/>pytest"]
    L["Code Quality<br/>Ruff"]
    M["GitHub Actions CI"]
    N["Recurring Pipeline<br/>Every 5 Minutes"]

    A --> B
    B --> C
    B --> D
    C --> E
    D --> F
    E --> G
    F --> G
    G --> H
    H --> I
    E --> I
    I --> J

    K --> M
    L --> M
    N -.-> B

    classDef source fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef raw fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef silver fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef gold fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
    classDef ci fill:#f3f4f6,stroke:#6b7280,color:#111827

    class A source
    class B,C,D raw
    class E,F,G,H silver
    class I,J gold
    class K,L,M,N ci
```

## Data Layers

| Layer | Purpose | Output |
|---|---|---|
| Raw | Preserve source data and historical snapshots | JSON |
| Silver | Structure, validate and prepare data for analysis | JSON and partitioned Parquet |
| Gold | Calculate station-level availability metrics | Analytical dataset |

## Processing

1. Retrieve station information and current station status from the BiciMAD GBFS API.
2. Store station metadata and timestamped status snapshots in the Raw layer.
3. Transform source data into structured Silver datasets.
4. Validate data quality before continuing the pipeline.
5. Convert historical station-status records into date-partitioned Parquet files.
6. Use PySpark to calculate station-level availability metrics.
7. Repeat the pipeline every five minutes and log execution failures.

## Quality and Continuous Integration

The project includes automated data quality checks, unit tests with pytest and code quality checks with Ruff. GitHub Actions executes the tests and lint checks on pushes and pull requests targeting the `main` branch.

## Future Extensions

Potential improvements include a dashboard for historical mobility analysis, additional transport data sources, cloud storage and querying, and natural-language analytics.