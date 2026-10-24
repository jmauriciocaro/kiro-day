"""Application configuration read from the environment.

No secrets or credentials are hardcoded. Values come from environment variables
(injected by SAM / Lambda) or, for the JWT secret, from AWS SSM Parameter Store
referenced by name.
"""
from __future__ import annotations

import functools
import os


class Settings:
    """Runtime settings loaded from environment variables."""

    def __init__(self) -> None:
        # DynamoDB single-table name.
        self.table_name: str = os.environ.get("POS_TABLE_NAME", "pos")
        # AWS region for the boto3 clients.
        self.aws_region: str = os.environ.get("AWS_REGION", "us-east-1")
        # Name of the SSM SecureString parameter that holds the JWT signing
        # secret. The value itself is never stored in code or the repo.
        self.jwt_secret_param: str = os.environ.get(
            "POS_JWT_SECRET_PARAM", "/pos/jwt-secret"
        )
        # Optional direct override for local development/testing only.
        self.jwt_secret_env: str | None = os.environ.get("POS_JWT_SECRET")
        # JWT settings.
        self.jwt_algorithm: str = os.environ.get("POS_JWT_ALGORITHM", "HS256")
        self.jwt_ttl_seconds: int = int(os.environ.get("POS_JWT_TTL_SECONDS", "3600"))
        # Optional local DynamoDB endpoint (e.g. DynamoDB Local / moto).
        self.dynamodb_endpoint_url: str | None = os.environ.get(
            "POS_DYNAMODB_ENDPOINT_URL"
        )


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
