from rest_framework import serializers

class CheckoutItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value = 1)


class CheckoutCreateSerializer(serializers.Serializer):
    items = CheckoutItemSerializer(many=True)
    shipping_address = serializers.CharField(max_length=255)
    billing_address = serializers.CharField(max_length = 255)