import logging
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import razorpay
import json
from apps.orders.models import Order
from apps.payments.services import PaymentService
from apps.payments.providers.razorpay_client import razorpay_client

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment_session(request, order_id):
    logger.info(
        "Create payment session API called",
        extra={"order_id": str(order_id), "user_id": str(request.user.id)},
    )

    order = get_object_or_404(Order, id=order_id, user=request.user)

    try:
        payment = PaymentService.create_checkout_session(order=order)
    except ValueError as exc:
        logger.warning(
            "Create payment session validation failed",
            extra={"order_id": str(order_id), "error": str(exc)},
        )
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "payment_id": str(payment.id),
            "order_id": str(order.id),
            "status": payment.status,
            "checkout_url": payment.checkout_url,
            "provider_session_id": payment.provider_session_id,
        },
        status=status.HTTP_201_CREATED,
    )

@api_view(["POST"])
@permission_classes([AllowAny])
def payment_webhook(request):
    payload = request.data
    event_type = payload.get("event_type")
    provider_session_id = payload.get("session_id")

    logger.info(
        "Payment webhook received",
        extra={
            "event_type": event_type,
            "provider_session_id": provider_session_id,
        },
    )

    try:
        if event_type == "payment.succeeded":
            payment = PaymentService.mark_payment_succeeded(
                provider_session_id=provider_session_id,
                provider_payload=payload,
            )
        elif event_type == "payment.failed":
            payment = PaymentService.mark_payment_failed(
                provider_session_id=provider_session_id,
                provider_payload=payload,
            )
        else:
            return Response({"message": "ignored"}, status=status.HTTP_200_OK)
    except ValueError as exc:
        logger.warning(
            "Payment webhook validation failed",
            extra={"error": str(exc), "payload": payload},
        )
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        logger.exception(
            "Unexpected error while processing payment webhook",
            extra={
                "event_type": event_type,
                "provider_session_id": provider_session_id,
            },
        )
        return Response(
            {
                "error": "Unable to process payment webhook",
                "code": "payment_webhook_internal_error",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return Response(
        {
            "message": "processed",
            "payment_id": str(payment.id),
            "status": payment.status,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@permission_classes([AllowAny])
def razorpay_webhook(request):
    signature = request.headers.get("X-Razorpay-Signature", "")
    event_id = request.headers.get("X-Razorpay-Event-Id", "")
    body = request.body

    # try:
    #     razorpay_client.utility.verify_webhook_signature(
    #         body,
    #         signature,
    #         settings.RAZORPAY_WEBHOOK_SECRET
    #     )
    # except razorpay.errors.SignatureVerificationError:
    #     return Response(
    #         {"error": "Invalid signature"},
    #         status=status.HTTP_400_BAD_REQUEST
    #     )

    try:
        payload = json.loads(body.decode("utf-8"))

        PaymentService.handle_razorpay_webhook(event_id = event_id, payload=payload,signature = signature)

        return Response({"message": "ok"}, status=status.HTTP_200_OK)

    except ValueError as exc:
        logger.warning(
            "Webhook validation failed",
            extra={"error": str(exc)}
        )
        return Response(
            {"error": str(exc)},
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception:
        logger.exception("Unexpected webhook error")

        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )