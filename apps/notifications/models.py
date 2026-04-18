import uuid

from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        ORDER_CONFIRMED = "order_confirmed", "Order Confirmed"
        ORDER_FAILED = "order_failed", "Order Failed"
        PAYMENT_SUCCEEDED = "payment_succeeded", "Payment Succeeded"
        PAYMENT_FAILED = "payment_failed", "Payment Failed"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_email = models.EmailField()
    type = models.CharField(max_length=50, choices=Type.choices)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    event_id = models.UUIDField()
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["event_id"]),
        ]