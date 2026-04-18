from rest_framework import serializers
from .models import Category,ProductImage,Product

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id", "name", "slug", "description",
            "is_active", "product_count", "created_at"
        )
        read_only_fields = ("id","slug","created_at")

    def get_product_count(self,obj):
        # counts products in this category
        # we'll optimize this with select_related later
        return obj.products.count() 

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image_url", "alt_text", "is_primary", "order")
        read_only_fields = ("id",)

class ProductListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views.
    Never return all fields in a list — too much data.
    """
    category_name = serializers.CharField(source="category.name",read_only=True)
    primary_image = serializers.SerializerMethodField()
    is_on_sale = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "price", "compare_at_price",
            "category_name", "primary_image", "is_on_sale",
            "discount_percentage", "is_featured", "status",
        )

    def get_primary_image(self,obj):
        # get the primary image or first image
        image = obj.images.filter(is_primary=True).first()
        if not image:
            image = obj.images.first()
        if image:
            return image.image_url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for detail views — includes nested data.
    This is what gets cached in Redis.
    """
    category = CategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    is_on_sale = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "description", "price",
            "compare_at_price", "sku", "status", "is_featured",
            "weight", "category", "category_id", "images",
            "is_on_sale", "discount_percentage",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")

    def validate_price(self,value):
        if value < 0:
            raise serializers.ValidationError("Price must be greater than zero")
        return value
    
    def validate(self,data):
        # cross-field validation
        compare_at = data.get("compare_at_price")
        price = data.get("price")
        if price and compare_price and compare_at <= price:
            raise serializers.ValidationError(
                "compare_at_price must be greater than price to show a discount"
            )
        return data



