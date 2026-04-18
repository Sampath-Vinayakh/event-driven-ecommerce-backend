import json
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Cache key constants - centralized so there never go out of sync
PRODUCT_DETAIL_KEY = "product:detail:{id}"
PRODUCT_LIST_KEY = "product:list:page:{page}"
CATEGORY_LIST_KEY = "category:list:all"

# TTLS in seconds
PRODUCT_DETAIL_TTL = 300
PRODUCT_LIST_TTL = 120
CATEGORY_LIST_TTL = 600

def get_cached_product_key(product_id: str):
    return PRODUCT_DETAIL_KEY.format(id=product_id)

def get_cached_product(product_id: str):
    """
    Cache-aside pattern — read path.

    1. Check Redis first
    2. On hit  → return cached data immediately (no DB call)
    3. On miss → return None (caller must fetch from DB and populate cache)
    """
    key = get_cached_product_key(product_id)

    try:
        cached = cache.get(key)
        if cached is not None:
            logger.debug(f"Cache HIT for product {product_id}")
            return cached
        logger.debug(f"Cache MISS for product {product_id}")
        return None
    except Exception as e: 
        logger.error(f"Cache read error for product {product_id}: {e}")
        return None

def set_cached_product(product_id: str, data: dict) -> None:
    """
    Cache-aside pattern — populate cache after DB read.
    Called by the view after a cache miss.
    """
    key = get_cached_product_key(product_id)
    try:
        cache.set(key,data,timeout=PRODUCT_DETAIL_TTL)
        logger.debug(f"Cache SET for product {product_id}, TTL={PRODUCT_DETAIL_TTL}s")
    except Exception as e:
        logger.error(f"Cache write error for product {product_id}: {e}")


def invalidate_product_cache(product_id: str) -> None:
    """
    Called when a product is updated or deleted.
    Removes stale data so the next read fetches fresh from DB.
    """
    key = get_cached_product_key(product_id)
    try:
        cache.delete(key)
        logger.debug(f"Cache INVALIDED for product {product_id}")
    except Exception as e:
        logger.error(f"Cache invalidation error for product {product_id}: {e}")





