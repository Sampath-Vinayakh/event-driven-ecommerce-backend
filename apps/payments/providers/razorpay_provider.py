import razorpay
from apps.payments.providers.razorpay_client import razorpay_client
from decimal import Decimal

class RazorpayProvider:
    
    @staticmethod
    def _to_paise(amount: Decimal) -> int:
        return int(amount * 100)

    @staticmethod
    def create_order(
        *,
        amount: Decimal,
        currency: str,
        receipt: str,
        notes: dict | None = None
    ) -> dict:
        payload = {
            "amount": RazorpayProvider._to_paise(amount),
            "currency": currency,
            "receipt": receipt,
            "notes": notes or {},
        }
        return razorpay_client.order.create(data=payload)