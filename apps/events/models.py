import uuid

from django.db import models


class OutboxEvent(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PUBLISHED = "published", "Published"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    event_type = models.CharField(max_length=100)
    aggregate_type = models.CharField(max_length=100)
    aggregate_id = models.UUIDField()

    payload = models.JSONField()
    metadata = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "outbox_events"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["aggregate_type", "aggregate_id"]),
            models.Index(fields=["event_type"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.aggregate_type}:{self.aggregate_id}"


class ProcessedEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.UUIDField()
    consumer_name = models.CharField(max_length=100)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "processed_events"
        constraints = [
            models.UniqueConstraint(
                fields=["event_id", "consumer_name"],
                name="unique_processed_event_per_consumer",
            )
        ]
        indexes = [
            models.Index(fields=["consumer_name", "processed_at"]),
        ]

    def __str__(self):
        return f"{self.consumer_name} - {self.event_id}"