"""DynamoDB single-table access layer for the `pos` table.

This module owns all item<->key mapping and DynamoDB calls. Business logic in
`services.py` depends on this abstraction, not on boto3 directly.

Task 4 implements product operations. Sale registration (Task 6) and daily
sales queries (Task 7) are added later in the same module.
"""
from __future__ import annotations

import json
from decimal import Decimal
from typing import List, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from app import keys
from app.config import Settings, get_settings
from app.errors import DuplicateSkuError, StockConflictError
from app.models import Product, ProductUpdate, Sale, SaleItem


def _to_decimal(value) -> Decimal:
    """DynamoDB stores numbers as Decimal; normalize incoming values."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


class Repository:
    """Data access for POS entities over a single DynamoDB table."""

    def __init__(self, settings: Optional[Settings] = None, table=None) -> None:
        self._settings = settings or get_settings()
        resource_kwargs = {"region_name": self._settings.aws_region}
        if self._settings.dynamodb_endpoint_url:
            resource_kwargs["endpoint_url"] = self._settings.dynamodb_endpoint_url

        if table is not None:
            # Test/explicit injection: use the given high-level Table, but build
            # an INDEPENDENT low-level client for transactions. Reusing
            # table.meta.client double-serializes manually-serialized payloads.
            self._table = table
        else:
            resource = boto3.resource("dynamodb", **resource_kwargs)
            self._table = resource.Table(self._settings.table_name)
        # A standalone low-level client for transact_write_items. It must not be
        # the resource's client (that one re-serializes our serialized items).
        self._client = boto3.client("dynamodb", **resource_kwargs)

    # --- Users ------------------------------------------------------------

    def upsert_user(self, username: str, password_hash: str, role: str) -> None:
        """Create or replace a user record (used by the seeding routine)."""
        self._table.put_item(
            Item={
                "PK": keys.user_pk(username),
                "SK": keys.user_sk(username),
                "type": "USER",
                "username": username,
                "passwordHash": password_hash,
                "role": role,
            }
        )

    def get_user(self, username: str) -> Optional[dict]:
        """Return the raw user item (username, passwordHash, role) or None."""
        response = self._table.get_item(
            Key={"PK": keys.user_pk(username), "SK": keys.user_sk(username)}
        )
        item = response.get("Item")
        if not item:
            return None
        return {
            "username": item["username"],
            "password_hash": item["passwordHash"],
            "role": item["role"],
        }

    # --- Products ---------------------------------------------------------

    def create_product(self, product: Product) -> Product:
        """Persist a new product; fail if the SKU already exists."""
        item = {
            "PK": keys.product_pk(product.sku),
            "SK": keys.product_sk(product.sku),
            "type": "PRODUCT",
            "sku": product.sku,
            "name": product.name,
            "price": _to_decimal(product.price),
            "stock": int(product.stock),
        }
        try:
            self._table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(PK)",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise DuplicateSkuError() from exc
            raise
        return product

    def get_product(self, sku: str) -> Optional[Product]:
        """Return the product for `sku`, or None if it does not exist."""
        response = self._table.get_item(
            Key={"PK": keys.product_pk(sku), "SK": keys.product_sk(sku)}
        )
        item = response.get("Item")
        if not item:
            return None
        return self._item_to_product(item)

    def list_products(self) -> List[Product]:
        """Return the full catalog.

        MVP uses a filtered Scan (small catalog). If the catalog grows, add a
        GSI on `type` and Query by prefix to avoid scanning.
        """
        products: List[Product] = []
        scan_kwargs = {
            "FilterExpression": "#t = :product",
            "ExpressionAttributeNames": {"#t": "type"},
            "ExpressionAttributeValues": {":product": "PRODUCT"},
        }
        while True:
            response = self._table.scan(**scan_kwargs)
            for item in response.get("Items", []):
                products.append(self._item_to_product(item))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key
        products.sort(key=lambda p: p.name.lower())
        return products

    def update_product(self, sku: str, update: ProductUpdate) -> Optional[Product]:
        """Update price and/or stock of an existing product.

        Returns the updated product, or None if the product does not exist.
        """
        set_parts = []
        names = {}
        values = {}
        if update.price is not None:
            set_parts.append("#p = :p")
            names["#p"] = "price"
            values[":p"] = _to_decimal(update.price)
        if update.stock is not None:
            set_parts.append("#s = :s")
            names["#s"] = "stock"
            values[":s"] = int(update.stock)
        if not set_parts:
            # Nothing to update; return the current product if it exists.
            return self.get_product(sku)

        try:
            response = self._table.update_item(
                Key={"PK": keys.product_pk(sku), "SK": keys.product_sk(sku)},
                UpdateExpression="SET " + ", ".join(set_parts),
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
                ConditionExpression="attribute_exists(PK)",
                ReturnValues="ALL_NEW",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return None
            raise
        return self._item_to_product(response["Attributes"])

    # --- Sales ------------------------------------------------------------

    def register_sale(self, sale: Sale) -> Sale:
        """Create the sale and decrement each product's stock atomically.

        Uses TransactWriteItems: one Put for the SALE item plus, per line, an
        Update that subtracts qty from stock guarded by `stock >= qty`. If any
        condition fails (including a concurrent race that empties stock), the
        whole transaction is cancelled and nothing is written.

        The sale line items are stored as a JSON string to keep the stored item
        flat (nested lists/maps complicate the low-level transact payload).
        """
        from boto3.dynamodb.types import TypeSerializer

        serializer = TypeSerializer()
        table_name = self._table.name

        day = sale.created_at[:10]  # yyyy-mm-dd from ISO-8601 timestamp
        items_json = json.dumps(
            [
                {
                    "sku": line.sku,
                    "name": line.name,
                    "qty": int(line.qty),
                    "unit_price": str(line.unit_price),
                }
                for line in sale.items
            ]
        )
        sale_item = {
            "PK": keys.sale_pk(day),
            "SK": keys.sale_sk(sale.created_at, sale.sale_id),
            "type": "SALE",
            "sale_id": sale.sale_id,
            "created_at": sale.created_at,
            "total": _to_decimal(sale.total),
            "payment_method": sale.payment_method,
            "payment_status": sale.payment_status,
            "cashier": sale.cashier,
            "items_json": items_json,
        }

        transact_items = [
            {
                "Put": {
                    "TableName": table_name,
                    "Item": {k: serializer.serialize(v) for k, v in sale_item.items()},
                }
            }
        ]
        for line in sale.items:
            transact_items.append(
                {
                    "Update": {
                        "TableName": table_name,
                        "Key": {
                            "PK": serializer.serialize(keys.product_pk(line.sku)),
                            "SK": serializer.serialize(keys.product_sk(line.sku)),
                        },
                        "UpdateExpression": "SET #stock = #stock - :qty",
                        "ConditionExpression": "attribute_exists(PK) AND #stock >= :qty",
                        "ExpressionAttributeNames": {"#stock": "stock"},
                        "ExpressionAttributeValues": {
                            ":qty": serializer.serialize(int(line.qty))
                        },
                    }
                }
            )

        try:
            self._client.transact_write_items(TransactItems=transact_items)
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code in ("TransactionCanceledException", "ConditionalCheckFailedException"):
                raise StockConflictError() from exc
            raise
        return sale

    def list_sales_by_day(self, day: str) -> List[Sale]:
        """Return all sales for `day` (yyyy-mm-dd), ordered chronologically.

        Query by the day's partition key; SK encodes the ISO timestamp so
        ascending order is chronological.
        """
        sales: List[Sale] = []
        query_kwargs = {
            "KeyConditionExpression": Key("PK").eq(keys.sale_pk(day)),
            "ScanIndexForward": True,
        }
        while True:
            response = self._table.query(**query_kwargs)
            for item in response.get("Items", []):
                sales.append(self._item_to_sale(item))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            query_kwargs["ExclusiveStartKey"] = last_key
        return sales

    @staticmethod
    def _item_to_sale(item: dict) -> Sale:
        raw_items = json.loads(item["items_json"])
        sale_items = [
            SaleItem(
                sku=line["sku"],
                qty=int(line["qty"]),
                name=line["name"],
                unit_price=_to_decimal(line["unit_price"]),
            )
            for line in raw_items
        ]
        return Sale(
            sale_id=item["sale_id"],
            created_at=item["created_at"],
            items=sale_items,
            total=_to_decimal(item["total"]),
            payment_method=item["payment_method"],
            payment_status=item["payment_status"],
            cashier=item["cashier"],
        )

    @staticmethod
    def _item_to_product(item: dict) -> Product:
        return Product(
            sku=item["sku"],
            name=item["name"],
            price=_to_decimal(item["price"]),
            stock=int(item["stock"]),
        )
