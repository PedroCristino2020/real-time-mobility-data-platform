
import os
from datetime import UTC, datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def main():
    endpoint_url = os.getenv(
        "S3_ENDPOINT_URL",
        "http://localhost:9000",
    )
    bucket = os.getenv("S3_BUCKET", "mobility-data")
    access_key = os.getenv("MINIO_ROOT_USER")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD")

    if not access_key or not secret_key:
        raise RuntimeError(
            "Faltan MINIO_ROOT_USER o MINIO_ROOT_PASSWORD en .env"
        )

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",
    )

    try:
        s3.head_bucket(Bucket=bucket)

        content = (
            "Conexion S3 correcta\n"
            f"Fecha UTC: {datetime.now(UTC).isoformat()}\n"
        )

        s3.put_object(
            Bucket=bucket,
            Key="raw/bicimad/test_connection.txt",
            Body=content.encode("utf-8"),
            ContentType="text/plain; charset=utf-8",
        )

        print(f"Conexion correcta con {endpoint_url}")
        print(
            "Archivo de prueba subido a "
            f"{bucket}/raw/bicimad/test_connection.txt"
        )

    except ClientError:
        print("Error al acceder al bucket.")
        raise


if __name__ == "__main__":
    main()
