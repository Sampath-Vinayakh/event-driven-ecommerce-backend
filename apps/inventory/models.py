import uuid

from django.db import models


class Inventory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.OneToOneField(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="inventory",
    )

    quantity_available = models.PositiveIntegerField(default=0)
    quantity_reserved = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self):
        return f"Inventory<{self.product.name}>"

    @property
    def total_quantity(self) -> int:
        return self.quantity_available + self.quantity_reserved

    def can_reserve(self, quantity: int) -> bool:
        return self.quantity_available >= quantity