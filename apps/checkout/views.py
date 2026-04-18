import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import CheckoutCreateSerializer
from .services import CheckoutService

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    serializer = CheckoutCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    logger.info(
        "Checkout create API called",
        extra={"user_id": str(request.user.id)},
    )

    success, result = CheckoutService.start_checkout(
        user=request.user,
        items=serializer.validated_data["items"],
        shipping_address=serializer.validated_data["shipping_address"],
        billing_address=serializer.validated_data["billing_address"],
    )

    if not success:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    return Response(result, status=status.HTTP_201_CREATED)