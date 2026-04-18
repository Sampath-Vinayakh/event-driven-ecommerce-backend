import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.events.kafka_producer import KafkaEventProducer
from apps.events.models import OutboxEvent

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5, default_retry_delay=10)
def publish_outbox_event_task(self, event_id: str):
    try:
        event = OutboxEvent.objects.filter(id=event_id).first()
        if not event:
            logger.warning(
                "Outbox event not found for publishing",
                extra={"event_id": event_id},
            )
            return

        if event.status == OutboxEvent.Status.PUBLISHED:
            logger.info(
                "Outbox event already published",
                extra={"event_id": event_id},
            )
            return

        producer = KafkaEventProducer()

        message = {
            "event_id": str(event.id),
            "event_type": event.event_type,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": str(event.aggregate_id),
            "payload": event.payload,
            "metadata": event.metadata,
            "created_at": event.created_at.isoformat(),
        }

        producer.publish(
            topic="domain-events",
            key=str(event.aggregate_id),
            value=message,
        )
        producer.flush()

        event.status = OutboxEvent.Status.PUBLISHED
        event.published_at = timezone.now()
        event.error_message = ""
        event.save(update_fields=["status", "published_at", "error_message", "updated_at"])

        logger.info(
            "Outbox event published successfully",
            extra={
                "event_id": str(event.id),
                "event_type": event.event_type,
            },
        )

    except Exception as exc:
        logger.exception(
            "Failed to publish outbox event",
            extra={"event_id": event_id},
        )

        OutboxEvent.objects.filter(id=event_id).update(
            status=OutboxEvent.Status.FAILED,
            error_message=str(exc),
        )
        raise self.retry(exc=exc)


@shared_task
def publish_pending_outbox_events():
    event_ids = list(
        OutboxEvent.objects.filter(status=OutboxEvent.Status.PENDING)
        .order_by("created_at")
        .values_list("id", flat=True)[:100]
    )

    for event_id in event_ids:
        publish_outbox_event_task.delay(str(event_id))