from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from . import dynamo
from .serializers import OrderEventSerializer, ProductSerializer


class ProductListView(APIView):
    def get(self, request: Request, category: str) -> Response:
        products = dynamo.list_products_by_category(category)
        data = [ProductSerializer(p).data for p in products]
        return Response(data)

    def post(self, request: Request, category: str) -> Response:
        ser = ProductSerializer(data={**request.data, "category": category})
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        product = dynamo.upsert_product(
            category=category,
            product_id=d["product_id"],
            name=d["name"],
            price_cents=d["price_cents"],
            stock=d.get("stock", 0),
            tags=d.get("tags", []),
        )
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    def get(self, request: Request, category: str, product_id: str) -> Response:
        try:
            product = dynamo.get_product(category, product_id)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(product).data)


class OrderHistoryView(APIView):
    def get(self, request: Request, order_id: str) -> Response:
        events = dynamo.get_order_history(order_id)
        return Response([OrderEventSerializer(e).data for e in events])

    def post(self, request: Request, order_id: str) -> Response:
        ser = OrderEventSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        event = dynamo.append_order_event(
            order_id=order_id,
            event_type=d["event_type"],
            user_id=d["user_id"],
            payload=d.get("payload", {}),
        )
        return Response(OrderEventSerializer(event).data, status=status.HTTP_201_CREATED)
