"""Claim combiner for merging extractor outputs and generating questions."""

from typing import Optional
from factchecker.core.models import ExtractedClaim
from factchecker.logging_config import get_logger

logger = get_logger(__name__)


class ClaimCombiner:
    """Combines outputs from TextExtractor and ImageExtractor into a single claim.
    
    This class merges text from multiple sources, generates granular questions
    for structured search, and combines confidence scores and metadata.
    """

    def __init__(self):
        """Initialize the ClaimCombiner."""
        pass

    async def combine(
        self,
        text_claim: Optional[ExtractedClaim],
        image_claim: Optional[ExtractedClaim],
    ) -> ExtractedClaim:
        """Combine extractor outputs into a single enhanced claim.
        
        Args:
            text_claim: Optional ExtractedClaim from TextExtractor
            image_claim: Optional ExtractedClaim from ImageExtractor
            
        Returns:
            ExtractedClaim with combined text, questions, metadata, and confidence.
            Returns low-confidence error claim if both inputs are None.
            
        Note:
            - If both claims are None, returns error claim with low confidence
            - Text merging logic will be implemented in task 2.5.2
            - Question generation will be implemented in task 2.5.3
            - Confidence merging will be implemented in task 2.5.4
        """
        logger.info(
            "Combining extractor outputs",
            extra={
                "has_text_claim": text_claim is not None,
                "has_image_claim": image_claim is not None,
            },
        )

        # Handle error case: both extractors returned None
        if text_claim is None and image_claim is None:
            logger.warning(
                "Both extractors returned None - returning error claim with low confidence"
            )
            return ExtractedClaim(
                claim_text="",
                extracted_from="hybrid",
                confidence=0.0,
                raw_input_type="both",
                metadata={
                    "error": "Both extractors failed",
                    "combination_method": "error_fallback",
                },
            )

        # Placeholder implementation - will be enhanced in tasks 2.5.2-2.5.4
        # For now, prefer text_claim if available, otherwise use image_claim
        if text_claim is not None:
            logger.debug("Using text_claim as primary source")
            # Return text_claim with minimal modifications for now
            # TODO: Implement text merging in task 2.5.2
            # TODO: Add questions in task 2.5.3
            # TODO: Merge confidence in task 2.5.4
            return text_claim
        elif image_claim is not None:
            logger.debug("Using image_claim as primary source")
            # Return image_claim with minimal modifications for now
            # TODO: Implement text merging in task 2.5.2
            # TODO: Add questions in task 2.5.3
            # TODO: Merge confidence in task 2.5.4
            return image_claim
        else:
            # This should not be reached due to the check above, but included for safety
            logger.error("Unexpected state: both claims are None after validation")
            return ExtractedClaim(
                claim_text="",
                extracted_from="hybrid",
                confidence=0.0,
                raw_input_type="both",
                metadata={
                    "error": "Unexpected error in claim combination",
                    "combination_method": "error_fallback",
                },
            )

