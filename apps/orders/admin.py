from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product",
        "product_name",
        "product_sku",
        "unit_price",
        "quantity",
        "subtotal",
        "created_at",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "total_amount",
        "currency",
        "created_at",
    )
    list_filter = ("status", "currency", "created_at")
    search_fields = ("id", "user__email")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "confirmed_at",
        "cancelled_at",
    )
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product_name",
        "quantity",
        "unit_price",
        "subtotal",
    )
    search_fields = ("order__id", "product_name", "product_sku")