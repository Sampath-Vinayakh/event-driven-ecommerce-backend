from .models import OutboxEvent
import logging
from django.db import transaction
from .tasks import publish_outbox_event_task
logger = logging.getLogger(__name__)

class EventService:
    @staticmethod
    def create_outbox_event(
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: dict[str,any],
        metadata: dict[str,any] = {}
    ) -> OutboxEvent:
        event = OutboxEvent.objects.create(
            event_type = event_type,
            aggregate_type = aggregate_type,
            aggregate_id = aggregate_id,
            payload = payload,
            metadata = metadata
        )
        transaction.on_commit(
            lambda: publish_outbox_event_task.delay(str(event.id))
        )
        logger.info(
                "Outbox event created",
                extra={
                    "event_id": str(event.id),
                    "event_type": event_type,
                    "aggregate_type": aggregate_type,
                    "aggregate_id": str(aggregate_id),
                },
            )

        return event