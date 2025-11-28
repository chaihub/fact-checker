"""Database layer for persistent storage."""

from typing import Optional
from factchecker.core.models import FactCheckResponse
from factchecker.logging_config import get_logger

logger = get_logger(__name__)


class Database:
    """SQLite database interface for fact-check results."""

    def __init__(self, db_path: str = "factchecker.db"):
        self.db_path = db_path
        # TODO: Initialize SQLite connection
        logger.info(f"Database initialized at {db_path}")

    async def save_response(
        self, claim_text: str, response: FactCheckResponse
    ) -> None:
        """Save fact-check response to database."""
        logger.info(f"Saving response for claim: {claim_text[:50]}...")
        # TODO: Implement database insert

    async def get_response(self, claim_text: str) -> Optional[FactCheckResponse]:
        """Retrieve cached response from database."""
        logger.debug(f"Looking up claim in database: {claim_text[:50]}...")
        # TODO: Implement database query
        return None

    async def close(self) -> None:
        """Close database connection."""
        logger.info("Database connection closed")
