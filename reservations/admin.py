from django.contrib import admin
from .models import RestaurantTable, Reservation
admin.site.register(RestaurantTable)
admin.site.register(Reservation)