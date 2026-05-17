from django.db import models

class TableZone(models.TextChoices):
    INTERIEUR = "interieur", "Intérieur"
    TERRASSE = "terrasse", "Terrasse"
    VIP = "vip", "VIP"
    FAMILLE = "famille", "Famille"
    BAR = "bar", "Bar"


class TableStatus(models.TextChoices):
    AVAILABLE = "available", "Disponible"
    RESERVED = "reserved", "Réservée"
    OCCUPIED = "occupied", "Occupée"
    NEEDS_CLEANING = "needs_cleaning", "À nettoyer"
    OUT_OF_SERVICE = "out_of_service", "Hors service"


class RestaurantTable(models.Model):
    name = models.CharField(max_length=50, unique=True)
    number = models.PositiveIntegerField(unique=True)
    zone = models.CharField(max_length=30, choices=TableZone.choices)
    capacity = models.PositiveIntegerField(default=2)
    status = models.CharField(
        max_length=30,
        choices=TableStatus.choices,
        default=TableStatus.AVAILABLE
    )

    pos_x = models.PositiveIntegerField(default=50)
    pos_y = models.PositiveIntegerField(default=50)

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["zone", "number"]

    def __str__(self):
        return f"{self.name} - {self.get_zone_display()}"