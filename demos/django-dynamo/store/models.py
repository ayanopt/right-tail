"""PynamoDB table definitions for the store domain."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from pynamodb.attributes import (
    ListAttribute,
    MapAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.models import Model


def _host() -> str | None:
    return os.environ.get("DYNAMODB_HOST") or None


class ProductTable(Model):
    """Products keyed by category (PK) + product_id (SK) for range queries."""

    class Meta:
        table_name = "products"
        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        host = _host()

    category = UnicodeAttribute(hash_key=True)
    product_id = UnicodeAttribute(range_key=True)
    name = UnicodeAttribute()
    price_cents = NumberAttribute()
    stock = NumberAttribute(default=0)
    tags = ListAttribute(of=UnicodeAttribute, default=list)
    created_at = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))


class OrderEventTable(Model):
    """Append-only order event log: PK=order_id, SK=ISO timestamp for range queries."""

    class Meta:
        table_name = "order_events"
        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        host = _host()

    order_id = UnicodeAttribute(hash_key=True)
    event_ts = UnicodeAttribute(range_key=True)  # ISO-8601, sortable
    event_type = UnicodeAttribute()              # CREATED | PAID | SHIPPED | CANCELLED
    payload = MapAttribute(default=dict)
    user_id = UnicodeAttribute()
