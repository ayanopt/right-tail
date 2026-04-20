"""Read/write helpers for DynamoDB tables. All public functions raise ValueError on bad input."""
from __future__ import annotations

from datetime import datetime, timezone

from pynamodb.exceptions import DoesNotExist

from .models import OrderEventTable, ProductTable


def get_product(category: str, product_id: str) -> ProductTable:
    try:
        return ProductTable.get(category, product_id)
    except DoesNotExist:
        raise ValueError(f"Product {category}/{product_id} not found")


def list_products_by_category(category: str, limit: int = 50) -> list[ProductTable]:
    return list(ProductTable.query(category, limit=limit))


def upsert_product(
    category: str,
    product_id: str,
    name: str,
    price_cents: int,
    stock: int = 0,
    tags: list[str] | None = None,
) -> ProductTable:
    item = ProductTable(
        category=category,
        product_id=product_id,
        name=name,
        price_cents=price_cents,
        stock=stock,
        tags=tags or [],
    )
    item.save()
    return item


def decrement_stock(category: str, product_id: str, quantity: int = 1) -> None:
    """Atomically decrement stock. Raises ValueError if stock would go negative."""
    product = get_product(category, product_id)
    if product.stock < quantity:
        raise ValueError("Insufficient stock")
    product.update(actions=[ProductTable.stock.set(product.stock - quantity)])


def append_order_event(
    order_id: str,
    event_type: str,
    user_id: str,
    payload: dict | None = None,
) -> OrderEventTable:
    ts = datetime.now(timezone.utc).isoformat()
    event = OrderEventTable(
        order_id=order_id,
        event_ts=ts,
        event_type=event_type,
        user_id=user_id,
        payload=payload or {},
    )
    event.save()
    return event


def get_order_history(order_id: str) -> list[OrderEventTable]:
    """Return all events for an order, sorted ascending by timestamp."""
    return list(OrderEventTable.query(order_id))
