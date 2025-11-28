"""In-memory and persistent caching layer."""

from typing import Optional, Any
from datetime import datetime, timedelta
from factchecker.core.models import FactCheckResponse
from factchecker.logging_config import get_logger

logger = get_logger(__name__)


class Cache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: dict = {}

    async def get(self, key: str) -> Optional[FactCheckResponse]:
        """Retrieve cached response by key."""
        if key not in self._cache:
            logger.debug(f"Cache miss for key: {key}")
            return None

        cached_item = self._cache[key]
        if datetime.now() > cached_item["expires_at"]:
            logger.debug(f"Cache expired for key: {key}")
            del self._cache[key]
            return None

        logger.info(f"Cache hit for key: {key}")
        return cached_item["value"]

    async def set(self, key: str, value: FactCheckResponse) -> None:
        """Store response in cache."""
        expires_at = datetime.now() + self.ttl
        self._cache[key] = {"value": value, "expires_at": expires_at}
        logger.info(f"Cached response for key: {key}")

    async def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
        logger.info("Cache cleared")

    def size(self) -> int:
        """Return cache size."""
        return len(self._cache)
