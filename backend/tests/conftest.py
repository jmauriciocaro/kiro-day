"""Shared pytest fixtures: a mocked DynamoDB single-table via moto."""
import boto3
import pytest
from moto import mock_aws

from app.config import Settings
from app.repository import Repository

TABLE_NAME = "pos-test"
REGION = "us-east-1"


@pytest.fixture
def dynamodb_table():
    """Create the single `pos` table in a mocked DynamoDB and yield it."""
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name=REGION)
        resource.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table = resource.Table(TABLE_NAME)
        table.wait_until_exists()
        yield table


@pytest.fixture
def repository(dynamodb_table):
    """A Repository bound to the mocked table."""
    settings = Settings()
    settings.table_name = TABLE_NAME
    settings.aws_region = REGION
    return Repository(settings=settings, table=dynamodb_table)
