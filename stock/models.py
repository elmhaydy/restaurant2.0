from django.db import models
from decimal import Decimal

class IngredientCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordering", "name"]
        verbose_name = "Catégorie d'ingrédient"
        verbose_name_plural = "Catégories d'ingrédients"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    UNIT_CHOICES = [
        ("g", "g"),
        ("kg", "kg"),
        ("ml", "ml"),
        ("l", "l"),
        ("piece", "pièce"),
    ]

    category = models.ForeignKey(
        IngredientCategory,
        on_delete=models.PROTECT,
        related_name="ingredients",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=150)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default="g"
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    alert_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name

    @property
    def is_low(self):
        return self.quantity <= self.alert_threshold

    @property
    def level(self):
        if self.quantity <= self.alert_threshold :
           return "faible"
        
        if self.quantity <= self.alert_threshold * Decimal("2"):
            return "moyen"
        
        return "correct"
    
    @property
    def level_label(self):
        if self.level == "faible":
            return "Faible"

        if self.level == "moyen":
            return "Moyen"

        return "Correct"
    
    @property
    def is_critical(self):
        return self.quantity <= 0

    @property
    def stock_percent(self):
        if self.alert_threshold <= 0:
            return 100

        percent = int((float(self.quantity) / float(self.alert_threshold * 3)) * 100)
        return max(0, min(percent, 100))


class StockMovement(models.Model):
    IN = "IN"
    OUT = "OUT"

    TYPES = [
        (IN, "Entrée"),
        (OUT, "Sortie"),
    ]

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="movements"
    )
    movement_type = models.CharField(max_length=3, choices=TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
