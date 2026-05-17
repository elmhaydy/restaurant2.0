from decimal import Decimal
from django.db import models
from django.conf import settings
from menu.models import Dish
from tables.models import RestaurantTable


class Order(models.Model):
    PENDING = 'PENDING'

    PREPARING = 'PREPARING'
    COOKING = 'COOKING'
    READY = 'READY'
    
    SERVED = 'SERVED'

    OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY'
    DELIVERED = 'DELIVERED'

    CANCELLED = 'CANCELLED'
    BILL_REQUESTED = 'BILL_REQUESTED'
    PAID = 'PAID'

    STATUS = [
        (PENDING, 'En attente'),
        (PREPARING, 'Préparation'),
        (COOKING, 'Cuisson'),
        (READY, 'Prête'),
        (SERVED, 'Servie'),
        (OUT_FOR_DELIVERY, 'En livraison'),
        (DELIVERED, 'Livrée'),
        (CANCELLED, 'Annulée'),
        (BILL_REQUESTED, 'Facture demandée'),
        (PAID, 'Payée'),
    ]

    ONSITE = 'ONSITE'
    TAKEAWAY = 'TAKEAWAY'
    DELIVERY = 'DELIVERY'

    MODES = [
        (ONSITE, 'Sur place'),
        (TAKEAWAY, 'À emporter'),
        (DELIVERY, 'Livraison'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    table = models.ForeignKey(
        RestaurantTable,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    mode = models.CharField(max_length=20, choices=MODES, default=ONSITE)
    status = models.CharField(max_length=30, choices=STATUS, default=PENDING, db_index=True)

    customer_name = models.CharField(max_length=160, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    delivery_address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'])
        ]

    @property
    def total(self):
        return sum((i.subtotal for i in self.items.all()), Decimal('0.00'))
    

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    dish_name = models.CharField(max_length=160, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    @property
    def display_name(self):
        if self.dish:
            return self.dish.name
        return self.dish_name or "Plat supprimé"

    def save(self, *args, **kwargs):
        if self.dish and not self.dish_name:
            self.dish_name = self.dish.name
        super().save(*args, **kwargs)
