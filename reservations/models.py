from django.db import models
from django.conf import settings
from tables.models import RestaurantTable

class ReservationStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    CONFIRMED = "confirmed", "Confirmée"
    CANCELLED = "cancelled", "Annulée"
    SEATED = "seated", "Client installé"
    DONE = "done", "Terminée"


class Reservation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    table = models.ForeignKey(RestaurantTable, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations")

    full_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30)

    date = models.DateField()
    time = models.TimeField()
    guests = models.PositiveIntegerField(default=2)
    table = models.ForeignKey(
            RestaurantTable,
            on_delete=models.SET_NULL,
            null=True,
            blank=True
    )
    message = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=ReservationStatus.choices, default=ReservationStatus.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.full_name} - {self.date} {self.time}"