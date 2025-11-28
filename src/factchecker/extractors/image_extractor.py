"""Image-based claim extractor with OCR."""

from typing import Optional
from factchecker.core.interfaces import BaseExtractor
from factchecker.core.models import ExtractedClaim
from factchecker.logging_config import get_logger

logger = get_logger(__name__)


class ImageExtractor(BaseExtractor):
    """Extracts claims from image input using OCR."""

    async def extract(
        self, claim_text: Optional[str], image_data: Optional[bytes]
    ) -> ExtractedClaim:
        """Extract structured claim from image via OCR."""
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

        # TODO: Implement OCR using pytesseract or similar
        # For now, return placeholder
        extracted_text = claim_text or "[OCR text would go here]"

        return ExtractedClaim(
            claim_text=extracted_text,
            extracted_from="image" if image_data else "text",
            confidence=0.8 if image_data else 1.0,
            raw_input_type=raw_input_type,
            metadata={
                "image_size": len(image_data) if image_data else 0,
                "ocr_confidence": 0.8 if image_data else None,
            },
        )
