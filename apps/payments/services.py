import logging
import uuid
from django.db import transaction
from django.utils import timezone

from apps.payments.models import Payment,PaymentWebhookEvent
from apps.orders.models import Order
from apps.inventory.services import InventoryService
from apps.orders.services import OrderService
from apps.events.services import EventService
from apps.payments.providers.razorpay_provider import RazorpayProvider
from django.conf import settings
from apps.payments.helpers import extract_payment_method_details
from apps.events.services import EventService


logger = logging.getLogger(__name__)

class PaymentService:
    @staticmethod
    @transaction.atomic
    def create_payment_record(*, order: Order) -> Payment:
        if order.status != Order.Status.PENDING:
            raise ValueError("Checkout session can only be created for pending orders.")

        active_payment = order.payments.filter(
            status__in=[Payment.Status.PENDING, Payment.Status.AUTHORIZED]
        ).first()
        if active_payment:
            raise ValueError("Active payment already exists for this order.")

        payment = Payment.objects.create(
            order=order,
            provider=Payment.Provider.RAZORPAY,
            status=Payment.Status.PENDING,
            amount=order.total_amount,
            currency="INR",
            idempotency_key=str(uuid.uuid4()),
            receipt=str(order.id),
            provider_notes={"order_id": str(order.id)},
        )
        return payment

    @staticmethod
    def create_provider_order(*, payment: Payment) -> dict:
        provider_response = RazorpayProvider.create_order(
            amount=payment.amount,
            currency=payment.currency,
            receipt=payment.receipt,
            notes={
                "internal_order_id": str(payment.order_id),
                "internal_payment_id": str(payment.id),
            },
        )

        payment.provider_order_id = provider_response["id"]
        payment.raw_provider_response = provider_response
        payment.save(
            update_fields=[
                "provider_order_id",
                "raw_provider_response",
                "updated_at",
            ]
        )

        return provider_response

    @staticmethod
    @transaction.atomic()
    def handle_razorpay_webhook(*, event_id: str = "", payload: dict, signature: str = "") -> None:
        if not event_id:
            raise ValueError("Missing X-Razorpay-Event-Id header")

        event_type = payload.get("event")

        if not event_type:
            raise ValueError("Missing webhook event type.")


        webhook_event, created = PaymentWebhookEvent.objects.get_or_create(
            event_id=event_id,
            defaults={
                "provider": Payment.Provider.RAZORPAY,
                "event_type": event_type,
                "signature": signature,
                "payload": payload,
            },
        )

        if not created and webhook_event.processed:
            logger.info(
                "Duplicate Razorpay webhook ignored",
                extra={"event_id": event_id, "event_type": event_type},
            )
            return

        payment_entity = (
            payload.get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )

        provider_payment_id = payment_entity.get("id", "")
        provider_order_id = payment_entity.get("order_id", "")

        if not provider_order_id:
            raise ValueError("Webhook payload missing provider order id.")

        payment = Payment.objects.select_for_update().filter(
            provider=Payment.Provider.RAZORPAY,
            provider_order_id=provider_order_id,
        ).first()

        if payment is None:
            raise ValueError("Payment not found for provider order id.")

        payment.provider_payment_id = provider_payment_id or payment.provider_payment_id
        payment.raw_webhook_payload = payload

        method, method_details = extract_payment_method_details(payment_entity)
        payment.method = method
        payment.method_details = method_details

        if event_type in {"payment.captured", "order.paid"}:
            if payment.status != Payment.Status.SUCCEEDED:
                payment.status = Payment.Status.SUCCEEDED
                payment.paid_at = timezone.now()
                payment.failure_code = ""
                payment.failure_message = ""

                payment.save(
                    update_fields=[
                        "provider_payment_id",
                        "raw_webhook_payload",
                        "method",
                        "method_details",
                        "status",
                        "paid_at",
                        "failure_code",
                        "failure_message",
                        "updated_at",
                    ]
                )
                items = [
                    {
                        "product_id": str(item.product_id),
                        "product_name": item.product_name,
                        "product_sku": item.product_sku,
                        "quantity": item.quantity
                    }
                    for item in payment.order.items.all()
                ]
                EventService.create_outbox_event(
                    event_type="payment.succeeded",
                    aggregate_type="payment",
                    aggregate_id=str(payment.id),
                    payload={
                        "payment_id": str(payment.id),
                        "order_id": str(payment.order_id),
                        "items": items,
                        "status": payment.status,
                        "amount": str(payment.amount),
                        "currency": payment.currency,
                        "provider": payment.provider,
                    },
                )
                # InventoryService.deduct_stock(order=payment.order)
                # OrderService.confirm_order(order=payment.order)

                logger.info(
                    "Payment marked succeeded from Razorpay webhook",
                    extra={
                        "payment_id": str(payment.id),
                        "order_id": str(payment.order_id),
                        "provider_payment_id": provider_payment_id,
                        "event_type": event_type,
                    },
                )
            else:
                payment.save(
                    update_fields=[
                        "provider_payment_id",
                        "raw_webhook_payload",
                        "method",
                        "method_details",
                        "updated_at",
                    ]
                )

        elif event_type == "payment.failed":
            error_code = payment_entity.get("error_code", "")
            error_description = payment_entity.get("error_description", "")

            if payment.status != Payment.Status.FAILED:
                payment.status = Payment.Status.FAILED
                payment.failed_at = timezone.now()
                payment.failure_code = error_code
                payment.failure_message = error_description

                payment.save(
                    update_fields=[
                        "provider_payment_id",
                        "raw_webhook_payload",
                        "method",
                        "method_details",
                        "status",
                        "failed_at",
                        "failure_code",
                        "failure_message",
                        "updated_at",
                    ]
                )
                items = [
                    {
                        "product_id": str(item.product_id),
                        "product_name": item.product_name,
                        "product_sku": item.product_sku,
                        "quantity": item.quantity
                    }
                    for item in payment.order.items.all()
                ]
                EventService.create_outbox_event(
                    event_type="payment.failed",
                    aggregate_type="payment",
                    aggregate_id=str(payment.id),
                    payload={
                        "payment_id": str(payment.id),
                        "order_id": str(payment.order_id),
                        "items": items,
                        "status": payment.status,
                        "failure_code": payment.failure_code,
                        "failure_message": payment.failure_message,
                        "provider": payment.provider,
                        "provider_payment_id": payment.provider_payment_id,
                        "amount": str(payment.amount),
                        "currency": payment.currency,
                    },
                )

                # InventoryService.release_stock(order=payment.order)
                # OrderService.fail_order(order=payment.order)

                logger.info(
                    "Payment marked failed from Razorpay webhook",
                    extra={
                        "payment_id": str(payment.id),
                        "order_id": str(payment.order_id),
                        "provider_payment_id": provider_payment_id,
                        "event_type": event_type,
                    },
                )
            else:
                payment.save(
                    update_fields=[
                        "provider_payment_id",
                        "raw_webhook_payload",
                        "method",
                        "method_details",
                        "updated_at",
                    ]
                )
        else:
            payment.save(
                update_fields=[
                    "provider_payment_id",
                    "raw_webhook_payload",
                    "method",
                    "method_details",
                    "updated_at",
                ]
            )

            logger.info(
                "Unhandled Razorpay webhook event ignored",
                extra={"event_type": event_type, "provider_order_id": provider_order_id},
            )

        webhook_event.processed = True
        webhook_event.processed_at = timezone.now()
        webhook_event.save(update_fields=["processed", "processed_at"])


    @staticmethod
    @transaction.atomic
    def mark_payment_succeeded(*, provider_session_id: str, provider_payload: dict) -> Payment:
        payment = (
            Payment.objects.select_for_update()
            .select_related("order")
            .filter(provider_session_id=provider_session_id)
            .first()
        )

        if payment is None:
            raise ValueError("Payment not found")

        if payment.status == Payment.Status.SUCCEEDED:
            logger.info(
                "Payment already marked as succeeded",
                extra={"payment_id": str(payment.id)},
            )
            return payment

        payment.status = Payment.Status.SUCCEEDED
        payment.provider_payment_id = provider_payload.get("payment_id", "")
        payment.raw_provider_response = provider_payload
        payment.paid_at = timezone.now()
        payment.save(
            update_fields=[
                "status",
                "provider_payment_id",
                "raw_provider_response",
                "paid_at",
                "updated_at",
            ]
        )
        EventService.create_outbox_event(
            event_type="payment.succeeded",
            aggregate_type="payment",
            aggregate_id=payment.id,
            payload={
                "payment_id": str(payment.id),
                "order_id": str(payment.order_id),
                "amount": str(payment.amount),
                "currency": payment.currency,
                "provider": payment.provider,
            },
        )
        InventoryService.deduct_stock(order=payment.order)
        OrderService.confirm_order(order=payment.order)


        logger.info(
            "Payment marked as succeeded",
            extra={
                "payment_id": str(payment.id),
                "order_id": str(payment.order_id),
            },
        )

        return payment

    @staticmethod
    @transaction.atomic
    def mark_payment_failed(*, provider_session_id: str, provider_payload: dict) -> Payment:
        payment = (
            Payment.objects.select_for_update()
            .select_related("order")
            .filter(provider_session_id=provider_session_id)
            .first()
        )

        if payment is None:
            raise ValueError("Payment not found")

        if payment.status == Payment.Status.FAILED:
            logger.info(
                "Payment already marked as failed",
                extra={"payment_id": str(payment.id)},
            )
            return payment

        payment.status = Payment.Status.FAILED
        payment.failure_code = provider_payload.get("failure_code", "")
        payment.failure_message = provider_payload.get("failure_message", "")
        payment.raw_provider_response = provider_payload
        payment.failed_at = timezone.now()
        payment.save(
            update_fields=[
                "status",
                "failure_code",
                "failure_message",
                "raw_provider_response",
                "failed_at",
                "updated_at",
            ]
        )

        InventoryService.release_stock(order=payment.order)
        OrderService.fail_order(order=payment.order)
        EventService.create_outbox_event(
            event_type="payment.failed",
            aggregate_type="payment",
            aggregate_id=payment.id,
            payload={
                "payment_id": str(payment.id),
                "order_id": str(payment.order_id),
                "provider": payment.provider,
                "failure_message": payment.failure_message,
            },
        )   
        logger.info(
            "Payment marked as failed",
            extra={
                "payment_id": str(payment.id),
                "order_id": str(payment.order_id),
            },
        )

        return payment

    @staticmethod
    def mark_failed(*, payment: Payment, reason: str | None = None) -> None:
        payment.status = Payment.Status.FAILED
        if reason:
            payment.failure_reason = reason
            payment.save(update_fields=["status", "failure_reason", "updated_at"])
        else:
            payment.save(update_fields=["status", "updated_at"])