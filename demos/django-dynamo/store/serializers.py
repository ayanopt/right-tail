from rest_framework import serializers


class ProductSerializer(serializers.Serializer):
    category = serializers.CharField()
    product_id = serializers.CharField()
    name = serializers.CharField()
    price_cents = serializers.IntegerField(min_value=0)
    stock = serializers.IntegerField(min_value=0, default=0)
    tags = serializers.ListField(child=serializers.CharField(), default=list)
    created_at = serializers.DateTimeField(read_only=True)


class OrderEventSerializer(serializers.Serializer):
    order_id = serializers.CharField(read_only=True)
    event_ts = serializers.CharField(read_only=True)
    event_type = serializers.CharField()
    user_id = serializers.CharField()
    payload = serializers.DictField(default=dict)
