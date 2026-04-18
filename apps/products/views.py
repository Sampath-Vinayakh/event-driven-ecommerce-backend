from django.shortcuts import render
import logging
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .cache import (
    get_cached_product,
    set_cached_product,
    invalidate_product_cache,
)
from .models import Product, Category
from .serializers import ProductListSerializer, ProductDetailSerializer, CategorySerializer

logger = logging.getLogger(__name__)

@api_view(["GET"])
@permission_classes([AllowAny])
def product_list(request):
    """
    Returns paginated list of active products.
    Supports filtering by category and featured flag.
    """
    queryset = Product.objects.filter(
        status=Product.Status.ACTIVE
    ).select_related(
        "category"
    ).prefetch_related(
        "images"
    )

    # Filtering
    category_slug = request.query_params.get("category")
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)
    filtered = request.query_params.get("filtered")
    if filtered == "true":
        queryset = queryset.filter(is_filtered=True)

    # Manual pagination
    page = int(request.query_params.get("page",1))
    page_size = 20
    start = (page - 1) * page_size
    end = start + page_size

    total = queryset.count()
    products = queryset[start:end]

    serializer = ProductListSerializer(products,many=True)

    return Response({
        "results": serializer.data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": -(-total // page_size),  # ceiling division
        }
    })

@api_view(["GET"])
@permission_classes([AllowAny])
def product_detail(request,product_id):
    """
    Cache-aside pattern in action:

    1. Check Redis for cached product data
    2. HIT  → return immediately, no DB call
    3. MISS → query DB, serialize, store in Redis, return
    """
    cached_product = get_cached_product(product_id)
    if cached_product is not None:
        # Cache HIT - return without touching the database
        logger.info(f"Serving product {product_id} from cache")
        return Response(cached_product)

    logger.info(f"Cache miss - fetching product {product_id} from db")
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images"),
        id=product_id,
        status=Product.Status.ACTIVE
    )

    serializer = ProductDetailSerializer(product)

    set_cached_product(str(product_id),serializer.data)

    return Response(serializer.data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def product_create(request):
    """Create a new product — staff only."""
    if not request.user.is_staff:
        return Response(
            {"error":"Staff access required"},
            status=status.HTTP_403_FORBIDDEN
        )
    serializer = ProductDetailSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data,status=HTTP_201_CREATED)

    return Response(serializer.errors,status=HTTP_400_BAD_REQUEST)

@api_view(["PUT","PATCH"])
@permission_classes([IsAuthenticated])
def product_update(request,product_id):
    """
    Update a product
    After updating invalidate the cache so stale data is cleared
    """
    if not request.user.is_staff:
        return Response(
            {"error":"Staff access required"},
            status = status.HTTP_403_FORBIDDEN
        )
    product = get_object_or_404(Product,id=product_id)
    partial = request.method == "PATCH"
    serializer = ProductDetailSerializer(product,data=request.data,partial=partial)

    if serializer.is_valid():
        serializer.save()

        # Invalidate cache after update

        invalidate_product_cache(str(product_id))
        logger.info(f"Product {product_id} updated - cache invalided")
        return Reponse(serializer.data)

    return Response(serializer.errors,status=HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def category_list(request):
    """Returns all active categories."""
    categories = Category.objects.filter(is_active=True)
    serializer  = CategorySerializer(categories,many=True)
    return Response(serializer.data)


