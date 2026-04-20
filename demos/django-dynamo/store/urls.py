from django.urls import path

from . import views

urlpatterns = [
    path("products/<str:category>/", views.ProductListView.as_view()),
    path("products/<str:category>/<str:product_id>/", views.ProductDetailView.as_view()),
    path("orders/<str:order_id>/events/", views.OrderHistoryView.as_view()),
]
