"""BlueSky API searcher (future implementation)."""

from typing import List
from factchecker.core.interfaces import BaseSearcher
from factchecker.core.models import SearchResult
from factchecker.logging_config import get_logger

logger = get_logger(__name__)


class BlueSkySearcher(BaseSearcher):
    """Searches BlueSky for relevant posts."""

    def __init__(self, handle: str = None, password: str = None):
        self.handle = handle
        self.password = password
        # TODO: Initialize BlueSky API client

    async def search(self, claim: str, query_params: dict) -> List[SearchResult]:
        """Search BlueSky for results."""
        logger.info(f"Searching BlueSky for claim: {claim[:50]}...")

        # TODO: Implement BlueSky API integration
        # For now, return empty list
        return []

    @property
    def platform_name(self) -> str:
        """Return platform identifier."""
        return "bluesky"
