"""Response generator for creating fact-check responses."""

from typing import List
from factchecker.core.models import (
    ExtractedClaim,
    SearchResult,
    VerdictEnum,
    Evidence,
    Reference,
)
from factchecker.logging_config import get_logger

logger = get_logger(__name__)


class ResponseGenerator:
    """Generates formatted fact-check responses."""

    async def generate(
        self,
        claim: ExtractedClaim,
        results: List[SearchResult],
        verdict: VerdictEnum,
        confidence: float,
        explanation: str,
    ) -> dict:
        """
        Generate complete fact-check response.

        Returns:
            Dictionary with verdict, evidence, references, and explanation
        """
        logger.info(
            f"Generating response: verdict={verdict}, confidence={confidence}"
        )

        # TODO: Implement response formatting and evidence extraction
        evidence = []
        references = []

        return {
            "verdict": verdict,
            "confidence": confidence,
            "evidence": evidence,
            "references": references,
            "explanation": explanation,
        }
