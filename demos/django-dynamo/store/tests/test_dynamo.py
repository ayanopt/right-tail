"""Tests using moto to mock DynamoDB."""
import os

import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")


@pytest.fixture(autouse=True)
def mock_dynamo():
    from moto import mock_aws
    with mock_aws():
        from store.models import OrderEventTable, ProductTable
        ProductTable.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
        OrderEventTable.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
        yield


def test_upsert_and_get_product():
    from store.dynamo import get_product, upsert_product
    upsert_product("electronics", "prod-1", "Laptop", 99900, stock=5)
    p = get_product("electronics", "prod-1")
    assert p.name == "Laptop"
    assert p.price_cents == 99900


def test_get_product_not_found():
    from store.dynamo import get_product
    with pytest.raises(ValueError, match="not found"):
        get_product("electronics", "missing")


def test_decrement_stock():
    from store.dynamo import decrement_stock, get_product, upsert_product
    upsert_product("electronics", "prod-2", "Phone", 49900, stock=3)
    decrement_stock("electronics", "prod-2", quantity=2)
    p = get_product("electronics", "prod-2")
    assert p.stock == 1


def test_decrement_stock_insufficient():
    from store.dynamo import decrement_stock, upsert_product
    upsert_product("electronics", "prod-3", "Tablet", 29900, stock=1)
    with pytest.raises(ValueError, match="Insufficient stock"):
        decrement_stock("electronics", "prod-3", quantity=5)


def test_order_event_append_and_query():
    from store.dynamo import append_order_event, get_order_history
    append_order_event("order-1", "CREATED", "user-42", {"items": 2})
    append_order_event("order-1", "PAID", "user-42", {"amount": 9900})
    history = get_order_history("order-1")
    assert len(history) == 2
    assert history[0].event_type == "CREATED"
    assert history[1].event_type == "PAID"
