import logging

from django.db import transaction

from apps.orders.models import Order
from .models import Inventory

logger = logging.getLogger(__name__)


class InventoryService:
    @staticmethod
    @transaction.atomic
    def reserve_stock(*, items: list[dict], order_id:str) -> None:
        """
        Reserve stock for every item in the order.

        Rule:
        - decrease quantity_available
        - increase quantity_reserved
        """
        logger.info(
            "Inventory reserve started",
            extra={
                "order_id": order_id,
                "item_count": len(items),
            },
        )

        for item in items:
            product_id = item["product_id"]
            product_name = item.get("product_name","")
            inventory = (
                Inventory.objects
                .select_for_update()
                .filter(product_id=product_id)
                .first()
            )

            if not inventory:
                logger.warning(
                    "Inventory record missing during reserve",
                    extra={
                        "order_id": order_id,
                        "product_id": product_id,
                        "product_name": product_name,
                    },
                )
                raise ValueError(f"Inventory record does not exist for product '{product_name}'.")

            if not inventory.can_reserve(item["quantity"]):
                logger.warning(
                    "Insufficient stock during reserve",
                    extra={
                        "order_id": order_id,
                        "product_id": str(product_id),
                        "product_name": product_name,
                        "requested_quantity": item["quantity"],
                        "quantity_available": inventory.quantity_available,
                        "quantity_reserved": inventory.quantity_reserved,
                    },
                )
                raise ValueError(f"Insufficient stock for product '{product_name}'.")

            before_available = inventory.quantity_available
            before_reserved = inventory.quantity_reserved

            inventory.quantity_available -= item["quantity"]
            inventory.quantity_reserved += item["quantity"]
            inventory.save(update_fields=["quantity_available", "quantity_reserved", "updated_at"])

            logger.info(
                "Inventory reserved successfully",
                extra={
                    "order_id": order_id,
                    "product_id": product_id,
                    "product_name": product_name,
                    "reserved_quantity": item["quantity"],
                    "before_available": before_available,
                    "after_available": inventory.quantity_available,
                    "before_reserved": before_reserved,
                    "after_reserved": inventory.quantity_reserved,
                },
            )

        logger.info(
            "Inventory reserve completed",
            extra={"order_id": order_id},
        )


    @staticmethod
    @transaction.atomic
    def release_stock(*, items: list[dict], order_id: str) -> None:
        logger.info(
            "Inventory release started",
            extra={
                "order_id": order_id,
                "item_count": len(items),
            },
        )

        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            product_name = item.get("product_name", "")

            inventory = (
                Inventory.objects
                .select_for_update()
                .filter(product_id=product_id)
                .first()
            )

            if not inventory:
                logger.warning(
                    "Inventory record missing during release",
                    extra={
                        "order_id": order_id,
                        "product_id": product_id,
                        "product_name": product_name,
                    },
                )
                raise ValueError(
                    f"Inventory record does not exist for product '{product_name or product_id}'."
                )

            if inventory.quantity_reserved < quantity:
                logger.error(
                    "Invalid reserved stock state during release",
                    extra={
                        "order_id": order_id,
                        "product_id": product_id,
                        "product_name": product_name,
                        "requested_release_quantity": quantity,
                        "quantity_reserved": inventory.quantity_reserved,
                    },
                )
                raise ValueError(
                    f"Reserved stock is inconsistent for product '{product_name or product_id}'."
                )

            before_available = inventory.quantity_available
            before_reserved = inventory.quantity_reserved

            inventory.quantity_available += quantity
            inventory.quantity_reserved -= quantity
            inventory.save(update_fields=["quantity_available", "quantity_reserved", "updated_at"])

            logger.info(
                "Inventory released successfully",
                extra={
                    "order_id": order_id,
                    "product_id": product_id,
                    "product_name": product_name,
                    "released_quantity": quantity,
                    "before_available": before_available,
                    "after_available": inventory.quantity_available,
                    "before_reserved": before_reserved,
                    "after_reserved": inventory.quantity_reserved,
                },
            )

        logger.info(
            "Inventory release completed",
            extra={"order_id": order_id},
        )

    @staticmethod
    @transaction.atomic
    def deduct_stock(*, items: list[dict], order_id: str) -> None:
        logger.info(
            "Inventory deduction started",
            extra={
                "order_id": order_id,
                "item_count": len(items),
            },
        )

        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            product_name = item.get("product_name", "")

            inventory = (
                Inventory.objects
                .select_for_update()
                .filter(product_id=product_id)
                .first()
            )

            if not inventory:
                logger.warning(
                    "Inventory record missing during deduction",
                    extra={
                        "order_id": order_id,
                        "product_id": product_id,
                        "product_name": product_name,
                    },
                )
                raise ValueError(
                    f"Inventory record does not exist for product '{product_name or product_id}'."
                )

            if inventory.quantity_reserved < quantity:
                logger.error(
                    "Invalid reserved stock state during deduction",
                    extra={
                        "order_id": order_id,
                        "product_id": product_id,
                        "product_name": product_name,
                        "requested_deduction_quantity": quantity,
                        "quantity_reserved": inventory.quantity_reserved,
                    },
                )
                raise ValueError(
                    f"Reserved stock is inconsistent for product '{product_name or product_id}'."
                )

            before_reserved = inventory.quantity_reserved

            inventory.quantity_reserved -= quantity
            inventory.save(update_fields=["quantity_reserved", "updated_at"])

            logger.info(
                "Inventory deducted successfully",
                extra={
                    "order_id": order_id,
                    "product_id": product_id,
                    "product_name": product_name,
                    "deducted_quantity": quantity,
                    "before_reserved": before_reserved,
                    "after_reserved": inventory.quantity_reserved,
                    "quantity_available": inventory.quantity_available,
                },
            )

        logger.info(
            "Inventory deduction completed",
            extra={"order_id": order_id},
        )