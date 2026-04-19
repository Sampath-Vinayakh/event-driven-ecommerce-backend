import json
import logging

from confluent_kafka import Consumer,KafkaError
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.events.models import ProcessedEvent
from apps.orders.models import Order
from apps.orders.services import OrderService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Consume payment events and update order state."

    def handle(self, *args, **options):
        consumer = Consumer(
            {
                "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "group.id": "orders-service",
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )

        topic = settings.KAFKA_EVENTS_TOPIC
        consumer.subscribe([topic])

        logger.info(
            "Order consumer started",
            extra={"topic": topic, "group_id": "orders-service"},
        )

        try:
            while True:
                msg = consumer.poll(1.0)

                if msg is None:
                    continue

                if msg.error():
                    err = msg.error()

                    if err.code() == KafkaError._PARTITION_EOF:
                        continue

                    elif err.code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                        logger.warning("Topic not available yet, retrying...")
                        time.sleep(2)
                        continue

                    else:
                        logger.error(
                            "Kafka consumer error: %s (code=%s, name=%s)",
                            err,
                            err.code(),
                            err.name(),
                        )
                        time.sleep(2)
                        continue

                try:
                    event = json.loads(msg.value().decode("utf-8"))

                    event_id = event.get("event_id")
                    event_type = event.get("event_type")
                    payload = event.get("payload", {})

                    if event_type not in {"payment.succeeded", "payment.failed"}:
                        consumer.commit(message=msg)
                        continue

                    order_id = payload.get("order_id")
                    if not event_id:
                        raise ValueError("event_id missing in Kafka message.")
                    if not order_id:
                        raise ValueError("order_id missing in event payload.")

                    with transaction.atomic():
                        processed, created = ProcessedEvent.objects.get_or_create(
                            event_id=event_id,
                            consumer_name="orders-service",
                        )

                        if not created:
                            logger.info(
                                "Duplicate event skipped",
                                extra={
                                    "event_id": event_id,
                                    "event_type": event_type,
                                    "order_id": order_id,
                                },
                            )
                            consumer.commit(message=msg)
                            continue

                        order = (
                            Order.objects.select_for_update()
                            .filter(id=order_id)
                            .first()
                        )

                        if order is None:
                            raise ValueError(f"Order not found for id={order_id}")

                        if event_type == "payment.succeeded":
                            if order.status != Order.Status.CONFIRMED:
                                OrderService.confirm_order(order=order)

                        elif event_type == "payment.failed":
                            if order.status != Order.Status.FAILED:
                                OrderService.fail_order(order=order)

                    consumer.commit(message=msg)

                    logger.info(
                        "Order event processed successfully",
                        extra={
                            "event_id": event_id,
                            "event_type": event_type,
                            "order_id": order_id,
                        },
                    )

                except Exception:
                    logger.exception(
                        "Failed to process order event",
                        extra={
                            "topic": msg.topic(),
                            "partition": msg.partition(),
                            "offset": msg.offset(),
                        },
                    )
                    # no commit - messages will be retried

        except KeyboardInterrupt:
            logger.info("Order consumer stopped manually.")
        finally:
            consumer.close()