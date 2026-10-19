
import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_s3_client():
    access_key = os.getenv("MINIO_ROOT_USER")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD")
    endpoint_url = os.getenv(
        "S3_ENDPOINT_URL",
        "http://localhost:9000",
    )

    if not access_key or not secret_key:
        raise RuntimeError(
            "Faltan MINIO_ROOT_USER o MINIO_ROOT_PASSWORD en .env"
        )

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",
    )


def upload_file(local_path: str | Path, object_key: str) -> None:
    bucket = os.getenv("S3_BUCKET", "mobility-data")
    client = get_s3_client()

    client.upload_file(
        str(local_path),
        bucket,
        object_key,
    )

    print(f"Uploaded to S3: s3://{bucket}/{object_key}")
