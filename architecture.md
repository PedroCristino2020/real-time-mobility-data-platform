# Architecture

Initial project architecture:

Data Sources
→ Python Ingestion
→ AWS S3 Bronze
→ PySpark ETL
→ S3 Silver
→ PySpark / SQL
→ Gold
→ Athena / PostgreSQL
→ Dashboard
→ Generative AI Layer