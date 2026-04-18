from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.products.models import Product, Category
from apps.inventory.models import Inventory
from apps.orders.services import OrderService
from apps.inventory.services import InventoryService
from apps.payments.services import PaymentService

User = get_user_model()


class Command(BaseCommand):
    help = "Test payment success and failure flows"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n🚀 Starting Payment Flow Tests...\n"))

        user = self.create_user()
        product = self.create_product()
        self.create_inventory(product)

        # ---------- SUCCESS FLOW ----------
        # self.stdout.write(self.style.WARNING("\n===== SUCCESS FLOW ====="))

        # order = self.create_order(user, product)
        # self.reserve_inventory(order)

        # payment = self.create_payment(order)

        # self.stdout.write(self.style.SUCCESS("\n--- Simulating PAYMENT SUCCESS ---"))
        # PaymentService.mark_payment_succeeded(
        #     provider_session_id=payment.provider_session_id,
        #     provider_payload={"payment_id": "success_123"},
        # )

        # self.verify_success(order, payment, product)

        # ---------- FAILURE FLOW ----------
        self.stdout.write(self.style.WARNING("\n===== FAILURE FLOW ====="))

        order2 = self.create_order(user, product)
        self.reserve_inventory(order2)

        payment2 = self.create_payment(order2)

        self.stdout.write(self.style.ERROR("\n--- Simulating PAYMENT FAILURE ---"))
        PaymentService.mark_payment_failed(
            provider_session_id=payment2.provider_session_id,
            provider_payload={
                "failure_code": "declined",
                "failure_message": "Card declined",
            },
        )

        self.verify_failure(order2, payment2, product)

        self.stdout.write(self.style.SUCCESS("\n🎉 ALL TESTS COMPLETED\n"))

    # ---------------- HELPERS ---------------- #

    def create_user(self):
        user, _ = User.objects.get_or_create(
            email="test@example.com",
            defaults={
                "first_name": "Test",
                "last_name": "User",
            },
        )
        user.set_password("password123")
        user.save()
        return user

    def create_product(self):
        category, _ = Category.objects.get_or_create(name="Test Category", slug="test-category")

        product, _ = Product.objects.get_or_create(
            name="Test Product",
            slug="test-product",
            sku="TEST123",
            category=category,
            defaults={
                "price": 100,
                "description": "Test product",
                "status": "active",
            },
        )
        return product

    def create_inventory(self, product):
        inventory, _ = Inventory.objects.get_or_create(
            product=product,
            defaults={
                "quantity_available": 10,
                "quantity_reserved": 0,
            },
        )
        return inventory

    def create_order(self, user, product):
        order = OrderService.create_order(
            user=user,
            items=[
                {
                    "product_id": str(product.id),
                    "quantity": 2,
                }
            ],
            shipping_address="Test Address",
            billing_address="Test Address",
        )
        self.stdout.write(f"Order created: {order.id}")
        return order

    def reserve_inventory(self, order):
        InventoryService.reserve_stock(order=order)
        self.stdout.write(f"Inventory reserve")

    def create_payment(self, order):
        payment = PaymentService.create_checkout_session(order=order)
        self.stdout.write(f"Payment created: {payment.id}")
        return payment

    # ---------------- VERIFICATION ---------------- #

    def verify_success(self, order, payment, product):
        order.refresh_from_db()
        payment.refresh_from_db()
        inventory = Inventory.objects.get(product=product)

        self.stdout.write("\n--- VERIFY SUCCESS ---")
        self.stdout.write(f"Payment status: {payment.status}")
        self.stdout.write(f"Order status: {order.status}")
        self.stdout.write(
            f"Inventory: available={inventory.quantity_available}, reserved={inventory.quantity_reserved}"
        )

    def verify_failure(self, order, payment, product):
        order.refresh_from_db()
        payment.refresh_from_db()
        inventory = Inventory.objects.get(product=product)

        self.stdout.write("\n--- VERIFY FAILURE ---")
        self.stdout.write(f"Payment status: {payment.status}")
        self.stdout.write(f"Order status: {order.status}")
        self.stdout.write(
            f"Inventory: available={inventory.quantity_available}, reserved={inventory.quantity_reserved}"
        )