from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.products.models import Product
from .models import Order, OrderItem
import logging
from apps.events.services import EventService

logger = logging.getLogger(__name__)


class OrderService:
    @staticmethod
    def calculate_totals(items_data: list[dict], shipping_amount=Decimal("0.00"), tax_amount=Decimal("0.00")):
        """
        items_data format:
        [
            {"product": <Product instance>, "quantity": 2},
            ...
        ]
        """
        subtotal_amount = Decimal("0.00")

        for item in items_data:
            product = item["product"]
            quantity = item["quantity"]
            subtotal_amount += product.price * quantity

        total_amount = subtotal_amount + shipping_amount + tax_amount

        return {
            "subtotal_amount": subtotal_amount,
            "shipping_amount": shipping_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
        }

    @staticmethod
    @transaction.atomic
    def create_order(
        *,
        user,
        items: list[dict],
        shipping_address: str = "",
        billing_address: str = "",
        notes: str = "",
        shipping_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
    ) -> Order:
        """
        items format:
        [
            {"product_id": "<uuid>", "quantity": 2},
            ...
        ]
        """
        logger.info(
            "Order creation started",
            extra={
                "user_id": str(user.id),
                "user_email": user.email,
                "item_count": len(items),
            },
        )
        if not items:
            logger.warning(
                "Order creation failed: empty items",
                extra={
                    "user_id": str(user.id),
                    "user_email": user.email,
                },
            )
            raise ValueError("Order must contain at least one item.")

        validated_items = []

        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity")

            if not product_id:
                logger.warning(
                    "Order creation failed: missing product_id",
                    extra={
                        "user_id": str(user.id),
                        "user_email": user.email,
                        "raw_item": item,
                    },
                )
                raise ValueError("Each item must include product_id.")

            if quantity is None or int(quantity) <= 0:
                logger.warning(
                    "Order creation failed: invalid quantity",
                    extra={
                        "user_id": str(user.id),
                        "user_email": user.email,
                        "product_id": str(product_id),
                        "quantity": quantity,
                    },
                )
                raise ValueError("Quantity must be greater than 0.")

            product = Product.objects.filter(id=product_id).first()

            if not product:
                logger.warning(
                    "Order creation failed: product not found",
                    extra={
                        "user_id": str(user.id),
                        "user_email": user.email,
                        "product_id": str(product_id),
                    },
                )
                raise ValueError(f"Invalid product_id: {product_id}")

            if product.status != Product.Status.ACTIVE:
                logger.warning(
                    "Order creation failed: inactive product",
                    extra={
                        "user_id": str(user.id),
                        "user_email": user.email,
                        "product_id": str(product.id),
                        "product_name": product.name,
                        "product_status": product.status,
                    },
                )
                raise ValueError(f"Product '{product.name}' is not available for ordering.")

            validated_items.append(
                {
                    "product": product,
                    "quantity": int(quantity),
                }
            )

        totals = OrderService.calculate_totals(
            validated_items,
            shipping_amount=shipping_amount,
            tax_amount=tax_amount,
        )

        logger.info(
            "Order totals calculated",
            extra={
                "user_id": str(user.id),
                "user_email": user.email,
                "subtotal_amount": str(totals["subtotal_amount"]),
                "shipping_amount": str(totals["shipping_amount"]),
                "tax_amount": str(totals["tax_amount"]),
                "total_amount": str(totals["total_amount"]),
            },
        )


        order = Order.objects.create(
            user=user,
            status=Order.Status.PENDING,
            shipping_address=shipping_address,
            billing_address=billing_address,
            notes=notes,
            subtotal_amount=totals["subtotal_amount"],
            shipping_amount=totals["shipping_amount"],
            tax_amount=totals["tax_amount"],
            total_amount=totals["total_amount"],
        )

        order_items = []
        for item in validated_items:
            product = item["product"]
            quantity = item["quantity"]
            subtotal = product.price * quantity

            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_sku=product.sku,
                    unit_price=product.price,
                    quantity=quantity,
                    subtotal=subtotal,
                )
            )

        OrderItem.objects.bulk_create(order_items)

        logger.info(
            "Order created successfully",
            extra={
                "order_id": str(order.id),
                "user_id": str(user.id),
                "user_email": user.email,
                "status": order.status,
                "item_count": len(order_items),
                "total_amount": str(order.total_amount),
            },
        )

        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(*, order: Order) -> Order:
        logger.info(
            "Order cancellation requested",
            extra={
                "order_id": str(order.id),
                "user_id": str(order.user.id),
                "user_email": order.user.email,
                "current_status": order.status,
            },
        )
        if not order.can_be_cancelled:
            logger.warning(
                "Order cancellation failed: invalid state",
                extra={
                    "order_id": str(order.id),
                    "user_id": str(order.user.id),
                    "user_email": order.user.email,
                    "current_status": order.status,
                },
            )
            raise ValueError(f"Order with status '{order.status}' cannot be cancelled.")

        order.status = Order.Status.CANCELLED
        order.cancelled_at = timezone.now()
        order.save(update_fields=["status", "cancelled_at", "updated_at"])

        logger.info(
            "Order cancelled successfully",
            extra={
                "order_id": str(order.id),
                "user_id": str(order.user.id),
                "user_email": order.user.email,
                "new_status": order.status,
                "cancelled_at": order.cancelled_at.isoformat(),
            },
        )

        return order

    @staticmethod
    @transaction.atomic
    def confirm_order(*, order: Order) -> Order:
        logger.info(
            "Order confirmation requested",
            extra={
                "order_id": str(order.id),
                "current_status": order.status,
            },
        )

        if order.status != Order.Status.PENDING:
            logger.warning(
                "Order confirmation failed: invalid state",
                extra={
                    "order_id": str(order.id),
                    "current_status": order.status,
                },
            )
            raise ValueError("Only pending orders can be confirmed.")

        order.status = Order.Status.CONFIRMED
        order.confirmed_at = timezone.now()
        order.save(update_fields=["status", "confirmed_at", "updated_at"])
        EventService.create_outbox_event(
            event_type="order.confirmed",
            aggregate_type="order",
            aggregate_id=order.id,
            payload={
                "order_id": str(order.id),
                "user_id": str(order.user_id),
                "total_amount": str(order.total_amount),
                "status": order.status,
            },
        )
        logger.info(
            "Order confirmed successfully",
            extra={
                "order_id": str(order.id),
                "new_status": order.status,
                "confirmed_at": order.confirmed_at.isoformat(),
            },
        )

        return order

    @staticmethod
    @transaction.atomic
    def fail_order(*, order: Order) -> Order:
        logger.info(
            "Order failure requested",
            extra={
                "order_id": str(order.id),
                "current_status": order.status,
            },
        )

        if order.status != Order.Status.PENDING:
            logger.warning(
                "Order failure update rejected: invalid state",
                extra={
                    "order_id": str(order.id),
                    "current_status": order.status,
                },
            )
            raise ValueError("Only pending orders can be marked as failed.")

        order.status = Order.Status.FAILED
        order.save(update_fields=["status", "updated_at"])
        EventService.create_outbox_event(
            event_type="order.failed",
            aggregate_type="order",
            aggregate_id=order.id,
            payload={
                "order_id": str(order.id),
                "user_id": str(order.user_id),
                "status": order.status,
            },
        )

        logger.info(
            "Order marked as failed",
            extra={
                "order_id": str(order.id),
                "new_status": order.status,
            },
        )

        return order