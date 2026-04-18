from rest_framework import serializers

from .models import Inventory


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Inventory
        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "quantity_available",
            "quantity_reserved",
            "total_quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields