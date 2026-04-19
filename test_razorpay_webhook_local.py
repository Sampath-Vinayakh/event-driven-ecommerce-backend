"""
Local Testing of Razorpay Webhook

Simulates Razorpay webhook requests against the local Django server.

Why this exists:
- Razorpay blocks tools like ngrok/webhook.site
- Allows end-to-end testing of payment flow locally

What it tests:
- payment.captured → success flow
- payment.failed → failure flow
- Duplicate event handling using event_id (idempotency)

Make sure:
- Django server is running on http://127.0.0.1:8000

Run:
    python test_razorpay_webhook_local.py
"""

import json
import requests

WEBHOOK_URL = "http://127.0.0.1:8000/api/payments/razorpay/webhook/"

def send_webhook(payload: dict, event_id: str):
    raw_body = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Event-Id": event_id,
        # Optional for now since signature validation is commented out
        "X-Razorpay-Signature": "local-test-signature",
    }

    response = requests.post(WEBHOOK_URL, data=raw_body, headers=headers)

    print(f"Event ID: {event_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print("-" * 80)


def build_payment_captured_payload(
    *,
    internal_order_id: str,
    internal_payment_id: str,
    razorpay_payment_id: str,
    razorpay_order_id: str,
    amount_paise: int = 30000,
):
    return {
        "entity": "event",
        "account_id": "acc_test_123456",
        "event": "payment.captured",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": razorpay_payment_id,          # provider payment id
                    "entity": "payment",
                    "amount": amount_paise,
                    "currency": "INR",
                    "status": "captured",
                    "order_id": razorpay_order_id,      # provider order id
                    "invoice_id": None,
                    "international": False,
                    "method": "upi",
                    "amount_refunded": 0,
                    "refund_status": None,
                    "captured": True,
                    "description": "Local webhook success test",
                    "card_id": None,
                    "bank": None,
                    "wallet": None,
                    "vpa": "success@testupi",
                    "email": "customer@example.com",
                    "contact": "9999999999",
                    "notes": {
                        "internal_order_id": internal_order_id,
                        "internal_payment_id": internal_payment_id,
                    },
                    "fee": 1000,
                    "tax": 180,
                    "error_code": None,
                    "error_description": None,
                    "error_source": None,
                    "error_step": None,
                    "error_reason": None,
                    "acquirer_data": {},
                    "created_at": 1710000000,
                }
            }
        }
    }


def build_payment_failed_payload(
    *,
    internal_order_id: str,
    internal_payment_id: str,
    razorpay_payment_id: str,
    razorpay_order_id: str,
    amount_paise: int = 60000,
):
    return {
        "entity": "event",
        "account_id": "acc_test_123456",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": razorpay_payment_id,          # provider payment id
                    "entity": "payment",
                    "amount": amount_paise,
                    "currency": "INR",
                    "status": "failed",
                    "order_id": razorpay_order_id,      # provider order id
                    "invoice_id": None,
                    "international": False,
                    "method": "card",
                    "amount_refunded": 0,
                    "refund_status": None,
                    "captured": False,
                    "description": "Local webhook failure test",
                    "card_id": None,
                    "bank": None,
                    "wallet": None,
                    "vpa": None,
                    "email": "customer@example.com",
                    "contact": "9999999999",
                    "notes": {
                        "internal_order_id": internal_order_id,
                        "internal_payment_id": internal_payment_id,
                    },
                    "fee": None,
                    "tax": None,
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Payment failed in local test flow",
                    "error_source": "customer",
                    "error_step": "payment_authentication",
                    "error_reason": "payment_declined",
                    "acquirer_data": {},
                    "created_at": 1710000001,
                }
            }
        }
    }


if __name__ == "__main__":
    # --------------------------------------------
    # TEST 1: SUCCESS FLOW
    # Replace with actual internal DB ids
    # --------------------------------------------
    success_internal_order_id = "a36e5d8e-3233-402e-bbc8-d05d996496b6"
    success_internal_payment_id = "d58eb529-3a86-4226-9867-efaeca879edf"

    success_payload = build_payment_captured_payload(
        internal_order_id=success_internal_order_id,
        internal_payment_id=success_internal_payment_id,
        razorpay_payment_id="pay_test_success_001",
        razorpay_order_id="order_SfGws8H0Xoemb7",
        amount_paise=60000,
    )

    print("1) Sending success webhook")
    send_webhook(
        payload=success_payload,
        event_id="evt_local_success_001",
    )

    print("2) Sending duplicate success webhook with SAME event id")
    send_webhook(
        payload=success_payload,
        event_id="evt_local_success_002",
    )

    # --------------------------------------------
    # TEST 2: FAILURE FLOW
    # Use a fresh pending order/payment pair
    # --------------------------------------------
    # failure_internal_order_id = "c97e6341-fee3-487a-a5c7-b4ea76263a8b"
    # failure_internal_payment_id = "69988e54-ffef-4035-912d-74afebe01693"

    # failure_payload = build_payment_failed_payload(
    #     internal_order_id=failure_internal_order_id,
    #     internal_payment_id=failure_internal_payment_id,
    #     razorpay_payment_id="pay_test_failed_001",
    #     razorpay_order_id="order_SdhivkghgMy4YI",
    #     amount_paise=50000,
    # )

    # print("3) Sending failure webhook")
    # send_webhook(
    #     payload=failure_payload,
    #     event_id="evt_local_failure_001",
    # )