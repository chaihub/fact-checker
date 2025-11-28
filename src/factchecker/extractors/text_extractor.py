"""Text-based claim extractor."""

from typing import Optional
from factchecker.core.interfaces import BaseExtractor
from factchecker.core.models import ExtractedClaim
from factchecker.logging_config import get_logger

logger = get_logger(__name__)


class TextExtractor(BaseExtractor):
    """Extracts claims from text input."""

    async def extract(
        self, claim_text: Optional[str], image_data: Optional[bytes]
    ) -> ExtractedClaim:
        """Extract structured claim from text."""
        if not claim_text and not image_data:
            raise ValueError(
                "At least one of claim_text or image_data must be provided"
            )

        # Determine input type
        if claim_text and image_data:
            raw_input_type = "both"
        elif image_data:
            raw_input_type = "image_only"
        else:
            raw_input_type = "text_only"

        # For now, just return the text as-is
        # Future: implement NLP-based claim extraction and segmentation
        return ExtractedClaim(
            claim_text=claim_text or "",
            extracted_from="text",
            confidence=1.0 if claim_text else 0.0,
            raw_input_type=raw_input_type,
            metadata={
                "text_length": len(claim_text) if claim_text else 0,
                "has_image": image_data is not None,
            },
        )
