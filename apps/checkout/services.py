import logging
from typing import Any

from apps.orders.services import OrderService
from apps.inventory.services import InventoryService
from apps.payments.services import PaymentService
from django.conf import settings
logger = logging.getLogger(__name__)


class CheckoutService:
    @staticmethod
    def start_checkout(
        *,
        user,
        items: list[dict[str, Any]],
        shipping_address: dict[str, Any],
        billing_address: dict[str, Any]
    ):
        order = None
        reservation_done = False

        logger.info(
            "Checkout started",
            extra={
                "user_id": str(user.id),
                "items_count": len(items)
            },
        )

        try:
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

            try:
                InventoryService.reserve_stock(items=inventory_items,order_id=str(order.id))
            except ValueError as e:
                logger.warning(
                    "Inventory reservation failed during checkout",
                    extra={"order_id": str(order.id), "reason": str(e)},
                )

                OrderService.fail_order(order=order)
                return False, {
                    "message": str(e),
                    "code": "inventory_reservation_failed",
                }

            reservation_done = True

            payment_data = PaymentService.create_checkout_session(
                order=order
            )

            logger.info(
                "Checkout session created successfully",
                extra={
                    "order_id": str(order.id),
                    "payment_id": payment_data["payment_id"],
                    "provider": payment_data["provider"],
                },
            )

            return True, {
                **payment_data
            }

        except Exception as exc:
            logger.exception(
                "Checkout orchestration failed",
                extra={
                    "user_id": str(user.id),
                    "order_id": str(order.id) if order else None,
                    "reservation_done": reservation_done,
                },
            )

            if order and reservation_done:
                try:
                    InventoryService.release_stock(order=order)
                except Exception:
                    logger.exception(
                        "Failed to release reserved stock after checkout failure",
                        extra={"order_id": str(order.id)},
                    )

            if order:
                try:
                    # reason=str(exc)
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