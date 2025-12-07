"""Text-based claim extractor."""

import re
import unicodedata
from typing import Optional, Tuple

import chardet

from factchecker.core.interfaces import BaseExtractor
from factchecker.core.models import ExtractedClaim
from factchecker.logging_config import get_logger

logger = get_logger(__name__)


class TextExtractor(BaseExtractor):
    """Extracts claims from text input."""

    # Text validation constants
    MIN_TEXT_LENGTH = 1
    MAX_TEXT_LENGTH = 1000

    async def extract(
        self, claim_text: Optional[str], image_data: Optional[bytes]
    ) -> ExtractedClaim:
        """Extract structured claim from text."""
        if claim_text is None and image_data is None:
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

        # Process text if provided
        normalized_text = ""
        validation_metadata: dict = {}
        original_text = claim_text or ""

        if claim_text is not None:
            # Normalize text
            normalized_text, was_normalized = self._normalize_text(claim_text)

            # Validate and clean text
            normalized_text, validation_metadata = self._validate_and_clean_text(
                normalized_text, was_normalized
            )

        # Collect metadata
        metadata = self._collect_metadata(
            original_text=original_text,
            normalized_text=normalized_text,
            image_data=image_data,
            validation_metadata=validation_metadata,
        )

        # Future: implement NLP-based claim extraction and segmentation (see section 2.4)
        # Confidence scoring will be implemented in section 2.4
        return ExtractedClaim(
            claim_text=normalized_text,
            extracted_from="text",
            confidence=1.0 if normalized_text else 0.0,
            raw_input_type=raw_input_type,
            metadata=metadata,
        )

    def _normalize_text(self, text: str) -> Tuple[str, bool]:
        """
        Normalize text by stripping whitespace, normalizing unicode, and collapsing whitespace.

        Args:
            text: Input text to normalize

        Returns:
            Tuple of (normalized_text, was_normalized) where was_normalized indicates
            if any normalization was applied
        """
        if not text:
            return "", False

        original_text = text
        normalized = False

        try:
            # Strip leading/trailing whitespace
            text = text.strip()
            if text != original_text:
                normalized = True

            # Normalize Unicode (NFKC: compatibility decomposition + composition)
            normalized_text = unicodedata.normalize("NFKC", text)
            if normalized_text != text:
                normalized = True
                text = normalized_text

            # Collapse multiple whitespace/newlines to single space
            collapsed_text = re.sub(r"\s+", " ", text)
            if collapsed_text != text:
                normalized = True
                text = collapsed_text

            return text, normalized

        except Exception as e:
            logger.warning(
                f"Text normalization failed: {e}. Returning original text.",
                exc_info=True,
            )
            return original_text, False

    def _validate_and_clean_text(
        self, text: str, was_normalized: bool
    ) -> Tuple[str, dict]:
        """
        Validate text length and handle edge cases.

        Args:
            text: Normalized text to validate
            was_normalized: Whether normalization was applied

        Returns:
            Tuple of (cleaned_text, validation_metadata)

        Raises:
            ValueError: If text is empty after normalization
        """
        validation_metadata: dict = {
            "normalized": was_normalized,
            "truncated": False,
        }

        # Check if text is empty after normalization
        if not text or len(text.strip()) == 0:
            raise ValueError(
                "Text is empty or contains only whitespace after normalization"
            )

        # Check if text exceeds maximum length
        if len(text) > self.MAX_TEXT_LENGTH:
            logger.warning(
                f"Text length ({len(text)}) exceeds maximum ({self.MAX_TEXT_LENGTH}). "
                "Truncating to maximum length."
            )
            text = text[: self.MAX_TEXT_LENGTH]
            validation_metadata["truncated"] = True

        # Check minimum length (after truncation)
        if len(text) < self.MIN_TEXT_LENGTH:
            raise ValueError(
                f"Text length ({len(text)}) is below minimum ({self.MIN_TEXT_LENGTH})"
            )

        return text, validation_metadata

    def _collect_metadata(
        self,
        original_text: str,
        normalized_text: str,
        image_data: Optional[bytes],
        validation_metadata: dict,
    ) -> dict:
        """
        Collect comprehensive metadata about the extracted text.

        Args:
            original_text: Original text before normalization
            normalized_text: Normalized text after processing
            image_data: Optional image data
            validation_metadata: Metadata from validation step

        Returns:
            Dictionary containing all metadata fields
        """
        metadata: dict = {
            "text_length": len(normalized_text),
            "original_text_length": len(original_text),
            "has_image": image_data is not None,
        }

        # Add validation metadata
        metadata.update(validation_metadata)

        # Word count (split on whitespace, filter empty strings)
        words = [w for w in normalized_text.split() if w]
        metadata["word_count"] = len(words)

        # Sentence count (approximate using regex for sentence endings)
        sentence_endings = re.findall(r"[.!?]+", normalized_text)
        metadata["sentence_count"] = len(sentence_endings) if sentence_endings else 1

        # Encoding detection (if we have bytes, otherwise assume UTF-8)
        if image_data:
            # If we have image data, we can't detect text encoding from it
            # This is handled by ImageExtractor
            metadata["encoding"] = "utf-8"  # Default assumption
        else:
            # For text input, Python 3 strings are already decoded
            # We assume UTF-8 encoding (standard for Python 3)
            metadata["encoding"] = "utf-8"

        return metadata
