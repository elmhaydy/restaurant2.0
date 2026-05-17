from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("cart/", views.cart_view, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("add/<int:dish_id>/", views.cart_add, name="cart_add"),
    path("remove/<int:dish_id>/", views.cart_remove, name="cart_remove"),
    path("increase/<int:dish_id>/", views.cart_increase, name="cart_increase"),
    path("decrease/<int:dish_id>/", views.cart_decrease, name="cart_decrease"),
    path("my-orders/", views.my_orders_view, name="my_orders"),
]