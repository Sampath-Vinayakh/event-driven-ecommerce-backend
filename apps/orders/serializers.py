from rest_framework import serializers

from .models import Order, OrderItem
from .services import OrderService


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "unit_price",
            "quantity",
            "subtotal",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "user_name",
            "status",
            "currency",
            "subtotal_amount",
            "shipping_amount",
            "tax_amount",
            "total_amount",
            "shipping_address",
            "billing_address",
            "notes",
            "items",
            "created_at",
            "updated_at",
            "confirmed_at",
            "cancelled_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "user_name",
            "status",
            "currency",
            "subtotal_amount",
            "shipping_amount",
            "tax_amount",
            "total_amount",
            "items",
            "created_at",
            "updated_at",
            "confirmed_at",
            "cancelled_at",
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()


class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemCreateSerializer(many=True)
    shipping_address = serializers.CharField(required=False, allow_blank=True)
    billing_address = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        request = self.context["request"]

        return OrderService.create_order(
            user=request.user,
            items=validated_data["items"],
            shipping_address=validated_data.get("shipping_address", ""),
            billing_address=validated_data.get("billing_address", ""),
            notes=validated_data.get("notes", ""),
        )