import uuid

from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        AUTHORIZED = "authorized", "Authorized"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    class Provider(models.TextChoices):
        DUMMY = "dummy", "Dummy"
        RAZORPAY = "razorpay", "Razorpay"

    class Method(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        CARD = "card", "Card"
        UPI = "upi", "UPI"
        NETBANKING = "netbanking", "Netbanking"
        WALLET = "wallet", "Wallet"
        EMI = "emi", "EMI"
        PAY_LATER = "pay_later", "Pay Later"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payments",
    )

    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        default=Provider.RAZORPAY,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    method = models.CharField(
        max_length=30,
        choices=Method.choices,
        default=Method.UNKNOWN,
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")

    idempotency_key = models.CharField(max_length=100, unique=True)

    provider_order_id = models.CharField(max_length=100, blank=True, db_index=True)
    provider_payment_id = models.CharField(max_length=100, blank=True, db_index=True)
    provider_signature = models.CharField(max_length=255, blank=True)

    receipt = models.CharField(max_length=100, blank=True, db_index=True)

    failure_code = models.CharField(max_length=100, blank=True)
    failure_message = models.TextField(blank=True)

    method_details = models.JSONField(default=dict, blank=True)

    provider_notes = models.JSONField(default=dict, blank=True)

    raw_provider_response = models.JSONField(default=dict, blank=True)
    raw_webhook_payload = models.JSONField(default=dict, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "status"]),
            models.Index(fields=["provider", "status"]),
            models.Index(fields=["provider", "provider_order_id"]),
            models.Index(fields=["provider", "provider_payment_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.order_id} - {self.provider} - {self.status}"


class PaymentWebhookEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=20, choices=Payment.Provider.choices)
    event_id = models.CharField(max_length=100, unique=True, db_index=True)
    event_type = models.CharField(max_length=100)
    signature = models.CharField(max_length=255, blank=True)

    payload = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_webhook_events"
        ordering = ["-created_at"]