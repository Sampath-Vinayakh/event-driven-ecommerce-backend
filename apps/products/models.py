from django.db import models
from django.utils.text import slugify
import uuid

class Category(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name = models.CharField(max_length=255,unique=True)
    slug = models.SlugField(max_length=255,unique=True,blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categories"
        verbose_name_plural = "categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.slug)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,   # prevent deleting a category that has products
        related_name="products"
    )
    name = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True             # original price for showing discounts
    )
    sku = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    is_featured = models.BooleanField(default=False)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_featured", "status"]), 
        ]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def is_on_sale(self):
        return (
            self.compare_at_price is not None
            and self.compare_at_price > self.price
        )

    @property
    def discount_percentage(self):
        if not self.is_on_sale:
            return 0
        discount = (self.compare_at_price - self.price) / self.compare_at_price
        return round(discount * 100, 2)

class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True,default = uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image_url = models.URLField(max_length=1000)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "product_images"
        ordering = ["order"]

    def __str__(self):
        return f"Image for {self.product.name}"



