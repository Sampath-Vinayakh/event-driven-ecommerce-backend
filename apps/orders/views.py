from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer
from .services import OrderService
import logging

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def order_create(request):
    logger.info(
        "Order create API called",
        extra={
            "user_id": str(request.user.id),
            "user_email": request.user.email,
        },
    )
    serializer = OrderCreateSerializer(data=request.data, context={"request": request})

    if serializer.is_valid():
        try:
            order = serializer.save()
        except ValueError as exc:
            logger.warning(
                "Order create API failed due to business validation",
                extra={
                    "user_id": str(request.user.id),
                    "user_email": request.user.email,
                    "error": str(exc),
                },
            )
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        logger.info(
            "Order create API succeeded",
            extra={
                "order_id": str(order.id),
                "user_id": str(request.user.id),
                "user_email": request.user.email,
            },
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
    logger.warning(
        "Order create API failed due to serializer validation",
        extra={
            "user_id": str(request.user.id),
            "user_email": request.user.email,
            "errors": serializer.errors,
        },
    )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items").order_by("-created_at")
    logger.info(
        "Order list API called",
        extra={
            "user_id": str(request.user.id),
            "user_email": request.user.email,
            "order_count": orders.count(),
        },
    )
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):
    logger.info(
        "Order detail API called",
        extra={
            "user_id": str(request.user.id),
            "user_email": request.user.email,
            "order_id": str(order_id),
        },
    )
    try:
        order = Order.objects.prefetch_related("items").get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        logger.warning(
            "Order detail API failed: order not found",
            extra={
                "user_id": str(request.user.id),
                "user_email": request.user.email,
                "order_id": str(order_id),
            },
        )
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = OrderSerializer(order)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def order_cancel(request, order_id):
    logger.info(
        "Order cancel API called",
        extra={
            "user_id": str(request.user.id),
            "user_email": request.user.email,
            "order_id": str(order_id),
        },
    )
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        logger.warning(
            "Order cancel API failed: order not found",
            extra={
                "user_id": str(request.user.id),
                "user_email": request.user.email,
                "order_id": str(order_id),
            },
        )
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        order = OrderService.cancel_order(order=order)
    except ValueError as exc:
        logger.warning(
            "Order cancel API failed due to business validation",
            extra={
                "user_id": str(request.user.id),
                "user_email": request.user.email,
                "order_id": str(order_id),
                "error": str(exc),
            },
        )
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    logger.info(
        "Order cancel API succeeded",
        extra={
            "user_id": str(request.user.id),
            "user_email": request.user.email,
            "order_id": str(order.id),
        },
    )
    return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)