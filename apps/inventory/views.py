from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Inventory
from .serializers import InventorySerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inventory_list(request):
    inventories = Inventory.objects.select_related("product").all().order_by("-created_at")
    serializer = InventorySerializer(inventories, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inventory_detail(request, product_id):
    inventory = (
        Inventory.objects
        .select_related("product")
        .filter(product_id=product_id)
        .first()
    )

    if not inventory:
        return Response({"error": "Inventory not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = InventorySerializer(inventory)
    return Response(serializer.data, status=status.HTTP_200_OK)