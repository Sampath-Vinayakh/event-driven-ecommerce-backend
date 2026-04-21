import logging
from typing import Any

from apps.orders.services import OrderService
from apps.inventory.services import InventoryService
from apps.payments.services import PaymentService
from django.conf import settings
from django.db import transaction
logger = logging.getLogger(__name__)


class CheckoutService:
    @staticmethod
    def start_checkout(
        *,
        user,
        items: list[dict[str, any]],
        shipping_address: dict[str, any],
        billing_address: dict[str, any],
    ):
        order = None
        payment = None
        db_step_committed = False
        inventory_items = None

        logger.info(
            "Checkout started",
            extra={
                "user_id": str(user.id),
                "items_count": len(items),
            },
        )

        try:
            with transaction.atomic():
                order = OrderService.create_order(
                    user=user,
                    items=items,
                    shipping_address=shipping_address,
                    billing_address=billing_address,
                )

                logger.info(
                    "Order created during checkout",
                    extra={"order_id": str(order.id), "user_id": str(user.id)},
                )

                inventory_items = [
                    {
                        "product_id": str(item.product_id),
                        "quantity": item.quantity,
                        "product_name": item.product_name,
                        "product_sku": item.product_sku,
                    }
                    for item in order.items.all()
                ]

                InventoryService.reserve_stock(
                    items=inventory_items,
                    order_id=str(order.id),
                )

            db_step_committed = True

            payment = PaymentService.create_payment_record(order=order)
            payment_data = PaymentService.create_provider_order(payment=payment)
            logger.info(
                "Checkout session created successfully",
                extra={
                    "order_id": str(order.id),
                    "provider_order_id": payment_data["provider_order_id"],
                    "provider": payment_data["provider"],
                },
            )

            return True, {
                "order_id": str(order.id),
                **payment_data,
            }

        except ValueError as exc:
            logger.warning(
                "Checkout failed due to business validation",
                extra={
                    "user_id": str(user.id),
                    "order_id": str(order.id) if order else None,
                    "payment_id": str(payment.id) if payment else None,
                    "error": str(exc),
                    "db_step_committed": db_step_committed,
                },
            )

            if payment:
                try:
                    PaymentService.mark_failed(payment=payment, reason=str(exc))
                except Exception:
                    logger.exception(
                        "Failed to mark payment as failed",
                        extra={"payment_id": str(payment.id)},
                    )

            if db_step_committed and order:
                try:
                    InventoryService.release_stock(items=inventory_items,order_id=str(order.id))
                except Exception:
                    logger.exception(
                        "Failed to release reserved stock after checkout failure",
                        extra={"order_id": str(order.id)},
                    )

                try:
                    OrderService.fail_order(order=order)
                except Exception:
                    logger.exception(
                        "Failed to mark order as failed after checkout failure",
                        extra={"order_id": str(order.id)},
                    )

            return False, {
                "message": str(exc),
                "code": "checkout_failed",
            }

        except Exception as exc:
            logger.exception(
                "Checkout orchestration failed",
                extra={
                    "user_id": str(user.id),
                    "order_id": str(order.id) if order else None,
                    "payment_id": str(payment.id) if payment else None,
                    "db_step_committed": db_step_committed,
                },
            )

            if payment:
                try:
                    PaymentService.mark_failed(payment=payment, reason=str(exc))
                except Exception:
                    logger.exception(
                        "Failed to mark payment as failed after checkout exception",
                        extra={"payment_id": str(payment.id)},
                    )

            if db_step_committed and order:
                try:
                    InventoryService.release_stock(items=inventory_items,order_id=str(order.id))
                except Exception:
                    logger.exception(
                        "Failed to release reserved stock after checkout failure",
                        extra={"order_id": str(order.id)},
                    )

                try:
                    OrderService.fail_order(order=order)
                except Exception:
                    logger.exception(
                        "Failed to mark order as failed after checkout failure",
                        extra={"order_id": str(order.id)},
                    )

            return False, {
                "message": "Unable to start checkout",
                "code": "checkout_failed",
                "details": str(exc),
            }