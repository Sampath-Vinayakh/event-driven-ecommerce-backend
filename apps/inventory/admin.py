from django.contrib import admin

from .models import Inventory


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "quantity_available",
        "quantity_reserved",
        "total_quantity",
        "updated_at",
    )
    search_fields = ("product__name", "product__sku")
    readonly_fields = ("id", "created_at", "updated_at", "total_quantity")