from django.urls import path
from . import views
app_name='reservations'
urlpatterns=[
    path("create/", views.create_reservation, name="create"),
    path("mes-reservations/", views.my_reservations, name="my_reservations"),
    path("mes-reservations/<int:reservation_id>/cancel/", views.cancel_my_reservation, name="cancel_my_reservation"),
    path("available-tables/", views.available_tables, name="available_tables"),
]
