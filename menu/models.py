from django.db import models
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name']
        verbose_name_plural = 'Catégories'

    def __str__(self):
        return self.name


class Dish(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='dishes'
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='dishes/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    manual_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['category__ordering', 'name']
        indexes = [
            models.Index(fields=['is_active', 'manual_available'])
        ]

    def __str__(self):
        return self.name

    @property
    def available(self):
        return self.is_active and self.manual_available
    
    @property
    def material_cost(self):
        return sum(
           (composition.cost for composition in self.composition.all()),
           Decimal("0.00")
        )


    @property
    def gross_margin(self):
        return self.price - self.material_cost


    @property
    def margin_percent(self):
        if self.price == 0:
           return Decimal("0.00")
        return (self.gross_margin / self.price) * 100
    

class DishIngredient(models.Model):
    UNIT_CHOICES = [
        ("g", "g"),
        ("kg", "kg"),
        ("ml", "ml"),
        ("l", "l"),
        ("piece", "pièce"),
    ]

    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name="composition"
    )

    ingredient = models.ForeignKey(
        "stock.Ingredient",
        on_delete=models.PROTECT,
        related_name="dish_usages"
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES
    )

    def __str__(self):
        return f"{self.dish.name} - {self.ingredient.name}"
    
    def converted_quantity(self):
        quantity = Decimal(self.quantity)

        if self.unit == self.ingredient.unit:
            return quantity

        conversions = {
            ("g", "kg"): Decimal("0.001"),
            ("kg", "g"): Decimal("1000"),
            ("ml", "l"): Decimal("0.001"),
            ("l", "ml"): Decimal("1000"),
        }

        factor = conversions.get((self.unit, self.ingredient.unit))

        if factor is None:
            return quantity

        return quantity * factor


    @property
    def cost(self):
        if not self.ingredient.unit_price:
            return Decimal("0.00")

        unit_price = Decimal(self.ingredient.unit_price)

        # For gram and milliliter stock units, the entered price is treated as
        # the price for 1000 g / 1000 ml to match common purchasing data.
        if self.ingredient.unit in {"g", "ml"}:
            unit_price = unit_price / Decimal("1000")

        return self.converted_quantity() * unit_price
