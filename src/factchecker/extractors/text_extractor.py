"""Text-based claim extractor."""

import asyncio
import json
import re
import unicodedata
from typing import Any, Optional, Tuple

import chardet

from factchecker.core.interfaces import BaseExtractor
from factchecker.core.llm_provider import GoogleGeminiProvider
from factchecker.core.models import ClaimQuestion, ExtractedClaim
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
        if claim_text is None:
            raise ValueError(
                "No text provided."
            )

        # Process text if provided
        normalized_text = ""
        validation_metadata: dict = {}
        original_text = claim_text

        # Normalize text
        # TODO: Check if this step adds value
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

        # Call LLM to extract and decompose claims into who/what/when/where/how/why
        questions: list[ClaimQuestion] = []
        segments: list[str] = []
        confidence = 0.0  # Default low confidence for fallback

        try:
            llm_result = await self._extract_with_llm(normalized_text)
            questions = llm_result["questions"]
            segments = llm_result["segments"]
            confidence = llm_result["confidence"]
        except Exception as e:
            logger.warning(
                f"LLM-based claim extraction failed: {e}. Using fallback extraction.",
                exc_info=True,
            )
            # Fallback: use text-only extraction without LLM decomposition

        return ExtractedClaim(
            claim_text=normalized_text,
            extracted_from="text",
            confidence=confidence,
            raw_input_type="text_only",
            questions=questions,
            segments=segments,
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

    async def _extract_with_llm(self, text: str) -> dict[str, Any]:
        """
        Extract and decompose claims using LLM (who/what/when/where/how/why).

        Args:
            text: Normalized text to extract claims from

        Returns:
            Dictionary with keys: questions (list[ClaimQuestion]), segments (list[str]), confidence (float)

        Raises:
            Exception: If LLM call fails or response is invalid
        """
        try:
            provider = GoogleGeminiProvider()
        except RuntimeError as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            raise

        # Call LLM with the claim_extraction_from_text use case
        llm_response = await provider.call(
            use_case="claim_extraction_from_text",
            prompt=text,
        )

        # Parse JSON response
        try:
            # Log the raw response for debugging
            logger.debug(f"Raw LLM response: {llm_response}")

            # Handle markdown code blocks (```json...```)
            response_text = llm_response.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            llm_data = json.loads(response_text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError(f"Invalid JSON from LLM: {e}") from e

        # Extract questions from who/what/when/where/how/why/platform elements
        questions: list[ClaimQuestion] = []
        element_types = ["who", "what", "when", "where", "how", "why", "platform"]

        for element_type in element_types:
            if element_type not in llm_data:
                continue

            element = llm_data[element_type]
            if not isinstance(element, dict):
                continue

            # Skip if element is marked as unknown
            if element.get("is_unknown", False):
                continue

            value = element.get("value", "").strip()
            if not value:
                continue

            question = ClaimQuestion(
                question_type=element_type,  # type: ignore
                answer_text=value,
                related_entity=element.get("related_entity"),
                confidence=float(element.get("confidence", 0.5)),
            )
            questions.append(question)

        # Extract key assertions
        segments = llm_data.get("key_assertions", [])
        if not isinstance(segments, list):
            segments = []

        # Extract overall confidence
        confidence = float(llm_data.get("overall_confidence", 0.5))

        return {
            "questions": questions,
            "segments": segments,
            "confidence": confidence,
        }
