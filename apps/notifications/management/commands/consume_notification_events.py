import json
import logging

from confluent_kafka import Consumer
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.events.models import ProcessedEvent
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from apps.orders.models import Order
from apps.payments.models import Payment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Consume domain events for notifications"

    def handle(self, *args, **options):
        consumer = Consumer(
            {
                "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "group.id": "notification-service",
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )
        consumer.subscribe(["domain-events"])

        logger.info("Notification consumer started")

        try:
            while True:
                msg = consumer.poll(1.0)

                if msg is None:
                    continue

                if msg.error():
                    logger.error(
                        "Kafka consumer error",
                        extra={"error": str(msg.error())},
                    )
                    continue

                try:
                    data = json.loads(msg.value().decode("utf-8"))
                    event_id = data["event_id"]
                    event_type = data["event_type"]
                    payload = data["payload"]

                    with transaction.atomic():
                        already_processed = ProcessedEvent.objects.filter(
                            event_id=event_id,
                            consumer_name="notification-service",
                        ).exists()

                        if already_processed:
                            logger.info(
                                "Event already processed by notification consumer",
                                extra={"event_id": event_id, "event_type": event_type},
                            )
                            consumer.commit(message=msg)
                            continue

                        self._handle_event(
                            event_id=event_id,
                            event_type=event_type,
                            payload=payload,
                        )

                        ProcessedEvent.objects.create(
                            event_id=event_id,
                            consumer_name="notification-service",
                        )

                    consumer.commit(message=msg)

                except Exception:
                    logger.exception("Failed to process notification event")
        finally:
            consumer.close()

    def _handle_event(self, *, event_id: str, event_type: str, payload: dict):
        if event_type == "order.confirmed":
            order = Order.objects.select_related("user").get(id=payload["order_id"])
            NotificationService.create_and_send_email(
                user_email=order.user.email,
                notification_type=Notification.Type.ORDER_CONFIRMED,
                subject="Your order has been confirmed",
                body=f"Your order {order.id} has been confirmed successfully.",
                event_id=event_id,
            )

        elif event_type == "order.failed":
            order = Order.objects.select_related("user").get(id=payload["order_id"])
            reason = payload.get("reason", "Unknown reason")
            NotificationService.create_and_send_email(
                user_email=order.user.email,
                notification_type=Notification.Type.ORDER_FAILED,
                subject="Your order could not be completed",
                body=f"Your order {order.id} failed. Reason: {reason}",
                event_id=event_id,
            )

        elif event_type == "payment.succeeded":
            payment = Payment.objects.select_related("order__user").get(id=payload["payment_id"])
            NotificationService.create_and_send_email(
                user_email=payment.order.user.email,
                notification_type=Notification.Type.PAYMENT_SUCCEEDED,
                subject="Payment received successfully",
                body=f"We received payment for order {payment.order.id}.",
                event_id=event_id,
            )

        elif event_type == "payment.failed":
            payment = Payment.objects.select_related("order__user").get(id=payload["payment_id"])
            reason = payload.get("failure_message", "Unknown reason")
            NotificationService.create_and_send_email(
                user_email=payment.order.user.email,
                notification_type=Notification.Type.PAYMENT_FAILED,
                subject="Payment failed",
                body=f"Payment for order {payment.order.id} failed. Reason: {reason}",
                event_id=event_id,
            )

        else:
            logger.info(
                "Ignoring unsupported notification event",
                extra={"event_id": event_id, "event_type": event_type},
            )