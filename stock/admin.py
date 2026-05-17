from django.contrib import admin
from .models import Ingredient, StockMovement


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "quantity", "unit", "unit_price", "alert_threshold", "is_low")
    search_fields = ("name",)
    list_filter = ("unit",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "movement_type", "quantity", "note", "created_at")
    search_fields = ("ingredient__name", "note")
    list_filter = ("movement_type", "created_at")