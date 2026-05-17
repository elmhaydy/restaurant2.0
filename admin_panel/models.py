# admin_panel/models.py
from django.db import models
from django.conf import settings

class ActivityLog(models.Model):
    ACTION_TYPES = [
        ("create", "Création"),
        ("update", "Modification"),
        ("delete", "Suppression"),
        ("login", "Connexion"),
        ("logout", "Déconnexion"),
        ("payment", "Paiement"),
        ("order", "Commande"),
        ("reservation", "Réservation"),
        ("stock", "Stock"),
        ("kitchen", "Cuisine"),
        ("table", "Table"),
        ("cleaning", "Nettoyage"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    module = models.CharField(max_length=100)
    description = models.TextField()
    object_id = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at} - {self.module} - {self.description}"
    

class RestaurantSettings(models.Model):
    restaurant_name = models.CharField(max_length=200, default="L'Héritage Gourmand")
    contact_email = models.EmailField(default="contact@lheritage.fr")
    phone_number = models.CharField(max_length=30, default="+33 1 23 45 67 89")
    address = models.CharField(max_length=255, blank=True)

    # Commandes
    online_orders_enabled = models.BooleanField(default=True)
    auto_accept_orders = models.BooleanField(default=False)
    notify_new_orders = models.BooleanField(default=True)

    # Réservations
    reservations_enabled = models.BooleanField(default=True)
    auto_confirm_reservations = models.BooleanField(default=False)
    max_reservation_people = models.PositiveIntegerField(default=10)

    # Tables
    table_assignment_required = models.BooleanField(default=True)
    auto_free_table_after_payment = models.BooleanField(default=True)

    # Cuisine
    kitchen_screen_enabled = models.BooleanField(default=True)
    notify_kitchen_new_order = models.BooleanField(default=True)

    # Paiement
    cash_payment_enabled = models.BooleanField(default=True)
    card_payment_enabled = models.BooleanField(default=True)
    online_payment_enabled = models.BooleanField(default=False)
    service_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Stock
    stock_management_enabled = models.BooleanField(default=True)
    notify_low_stock = models.BooleanField(default=True)
    block_order_if_stock_low = models.BooleanField(default=False)

    # Système
    maintenance_mode = models.BooleanField(default=False)
    activity_logs_enabled = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paramètres restaurant"
        verbose_name_plural = "Paramètres restaurant"

    def __str__(self):
        return "Paramètres système"