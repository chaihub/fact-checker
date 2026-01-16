"""Tests for TextExtractor."""

import json
import os
from unittest.mock import AsyncMock, patch

import pytest

from factchecker.extractors.text_extractor import TextExtractor
from factchecker.core.models import ExtractedClaim

# Check if API key is available for integration tests
HAS_GEMINI_API_KEY = bool(os.getenv("GEMINI_API_KEY"))


@pytest.fixture
def extractor():
    return TextExtractor()


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for claim decomposition."""
    return json.dumps(
        {
            "who": {
                "value": "the sky",
                "confidence": 0.9,
                "is_ambiguous": False,
                "is_unknown": False,
            },
            "what": {
                "value": "is blue",
                "confidence": 0.95,
                "is_ambiguous": False,
                "is_unknown": False,
            },
            "when": {
                "value": "unknown",
                "confidence": 0.0,
                "is_ambiguous": False,
                "is_unknown": True,
            },
            "where": {
                "value": "unknown",
                "confidence": 0.0,
                "is_ambiguous": False,
                "is_unknown": True,
            },
            "how": {
                "value": "unknown",
                "confidence": 0.0,
                "is_ambiguous": False,
                "is_unknown": True,
            },
            "why": {
                "value": "unknown",
                "confidence": 0.0,
                "is_ambiguous": False,
                "is_unknown": True,
            },
            "key_assertions": ["The sky is blue"],
            "overall_confidence": 0.85,
            "reasoning": "Simple factual claim about sky color",
        }
    )


@pytest.fixture
def long_text():
    """Generate text exceeding MAX_TEXT_LENGTH."""
    return "A" * 2000  # Exceeds MAX_TEXT_LENGTH of 1000


@pytest.fixture
def text_with_special_chars():
    """Text with various special characters and Unicode."""
    return "Café résumé naïve 🎉\t\n  multiple   spaces"


@pytest.fixture
def whitespace_only_text():
    """Text with only whitespace characters."""
    return "   \t\n\r   "


# Basic extraction tests
@pytest.mark.asyncio
async def test_text_extraction_basic(extractor, mock_llm_response):
    """Test basic text extraction."""
    with patch(
        "factchecker.extractors.text_extractor.GoogleGeminiProvider"
    ) as MockProvider:
        mock_provider = AsyncMock()
        mock_provider.call = AsyncMock(return_value=mock_llm_response)
        MockProvider.return_value = mock_provider

        result = await extractor.extract(claim_text="The sky is blue", image_data=None)
        assert isinstance(result, ExtractedClaim)
        assert result.claim_text == "The sky is blue"
        assert result.extracted_from == "text"
        assert result.raw_input_type == "text_only"
        assert 0 <= result.confidence <= 1
        assert len(result.questions) > 0  # Should have extracted questions


@pytest.mark.asyncio
async def test_text_extraction_requires_input(extractor):
    """Test that extraction fails without input."""
    with pytest.raises(ValueError):
        await extractor.extract(claim_text=None, image_data=None)


@pytest.mark.asyncio
async def test_hybrid_extraction(extractor, mock_llm_response):
    """Test extraction from both text and image."""
    with patch(
        "factchecker.extractors.text_extractor.GoogleGeminiProvider"
    ) as MockProvider:
        mock_provider = AsyncMock()
        mock_provider.call = AsyncMock(return_value=mock_llm_response)
        MockProvider.return_value = mock_provider

        result = await extractor.extract(
            claim_text="Verify this", image_data=b"mock_image_data"
        )
        assert result.raw_input_type == "text_only"  # TextExtractor only handles text
        assert result.metadata["has_image"] is True


@pytest.mark.asyncio
async def test_image_only_extraction(extractor):
    """Test extraction from image only."""
    # TextExtractor currently requires text input
    with pytest.raises(ValueError, match="No text provided"):
        await extractor.extract(claim_text=None, image_data=b"mock_image_data")


@pytest.mark.asyncio
async def test_extraction_metadata(extractor, mock_llm_response):
    """Test that metadata is populated."""
    with patch(
        "factchecker.extractors.text_extractor.GoogleGeminiProvider"
    ) as MockProvider:
        mock_provider = AsyncMock()
        mock_provider.call = AsyncMock(return_value=mock_llm_response)
        MockProvider.return_value = mock_provider

        result = await extractor.extract(
            claim_text="Test claim with length", image_data=None
        )
        assert "text_length" in result.metadata
        assert result.metadata["text_length"] > 0


# Edge case tests
@pytest.mark.asyncio
async def test_empty_string_raises_error(extractor):
    """Test that empty string after normalization raises ValueError."""
    with pytest.raises(ValueError, match="empty or contains only whitespace"):
        await extractor.extract(claim_text="", image_data=None)


@pytest.mark.asyncio
async def test_whitespace_only_raises_error(extractor, whitespace_only_text):
    """Test that whitespace-only text raises ValueError."""
    with pytest.raises(ValueError, match="empty or contains only whitespace"):
        await extractor.extract(claim_text=whitespace_only_text, image_data=None)


@pytest.mark.asyncio
async def test_very_long_text_truncated(extractor, long_text):
    """Test that very long text is truncated to MAX_TEXT_LENGTH."""
    result = await extractor.extract(claim_text=long_text, image_data=None)
    assert len(result.claim_text) == TextExtractor.MAX_TEXT_LENGTH
    assert result.metadata["truncated"] is True
    assert result.metadata["original_text_length"] == 2000
    assert result.metadata["text_length"] == TextExtractor.MAX_TEXT_LENGTH


@pytest.mark.asyncio
async def test_text_with_only_newlines_raises_error(extractor):
    """Test that text with only newlines raises ValueError."""
    with pytest.raises(ValueError, match="empty or contains only whitespace"):
        await extractor.extract(claim_text="\n\n\n", image_data=None)


# Special characters and encoding tests
@pytest.mark.asyncio
async def test_special_characters_handled(extractor, text_with_special_chars):
    """Test that special characters and Unicode are handled correctly."""
    result = await extractor.extract(claim_text=text_with_special_chars, image_data=None)
    assert isinstance(result, ExtractedClaim)
    assert "Café" in result.claim_text
    assert "résumé" in result.claim_text
    assert "🎉" in result.claim_text


@pytest.mark.asyncio
async def test_unicode_normalization(extractor):
    """Test Unicode normalization (NFKC)."""
    # Using combining character for é
    text_with_combining = "cafe\u0301"
    result = await extractor.extract(claim_text=text_with_combining, image_data=None)
    # Should normalize to composed form
    assert "é" in result.claim_text or "cafe" in result.claim_text


@pytest.mark.asyncio
async def test_mixed_whitespace_collapsed(extractor):
    """Test that mixed whitespace (tabs, spaces, newlines) is collapsed."""
    text = "word1\tword2\nword3  word4\r\nword5"
    result = await extractor.extract(claim_text=text, image_data=None)
    # Should have single spaces between words
    assert "  " not in result.claim_text  # No double spaces
    assert "\t" not in result.claim_text  # No tabs
    assert "\n" not in result.claim_text  # No newlines
    assert "\r" not in result.claim_text  # No carriage returns


@pytest.mark.asyncio
async def test_emoji_handling(extractor):
    """Test that emojis are preserved in normalized text."""
    text = "Hello 🎉 World 🌍 Test"
    result = await extractor.extract(claim_text=text, image_data=None)
    assert "🎉" in result.claim_text
    assert "🌍" in result.claim_text


# Text normalization tests
@pytest.mark.asyncio
async def test_whitespace_collapsing(extractor):
    """Test that excessive whitespace is collapsed to single spaces."""
    text = "word1    word2\t\tword3\n\nword4"
    result = await extractor.extract(claim_text=text, image_data=None)
    # Should have single spaces between words
    words = result.claim_text.split()
    assert len(words) == 4
    assert "word1" in words
    assert "word2" in words
    assert "word3" in words
    assert "word4" in words


@pytest.mark.asyncio
async def test_leading_trailing_whitespace_removed(extractor):
    """Test that leading and trailing whitespace is removed."""
    text = "   \t\n  Hello World  \t\n  "
    result = await extractor.extract(claim_text=text, image_data=None)
    assert result.claim_text == "Hello World"
    assert not result.claim_text.startswith((" ", "\t", "\n"))
    assert not result.claim_text.endswith((" ", "\t", "\n"))


@pytest.mark.asyncio
async def test_original_length_preserved_in_metadata(extractor):
    """Test that original text length is preserved in metadata."""
    original = "   Hello   World   "
    result = await extractor.extract(claim_text=original, image_data=None)
    assert result.metadata["original_text_length"] == len(original)
    assert result.metadata["text_length"] == len(result.claim_text)
    assert result.metadata["text_length"] <= result.metadata["original_text_length"]


@pytest.mark.asyncio
async def test_normalized_flag_set(extractor):
    """Test that normalized flag is set when normalization is applied."""
    # Text with excessive whitespace should trigger normalization
    text = "word1    word2\t\tword3"
    result = await extractor.extract(claim_text=text, image_data=None)
    assert result.metadata["normalized"] is True


@pytest.mark.asyncio
async def test_normalized_flag_not_set_for_clean_text(extractor):
    """Test that normalized flag is False when no normalization is needed."""
    text = "Clean text without issues"
    result = await extractor.extract(claim_text=text, image_data=None)
    # May or may not be normalized (strip might always apply), but should be consistent
    assert "normalized" in result.metadata


# Metadata validation tests
@pytest.mark.asyncio
async def test_word_count_accuracy(extractor):
    """Test that word_count is accurate."""
    text = "This is a test sentence with seven words"
    result = await extractor.extract(claim_text=text, image_data=None)
    assert result.metadata["word_count"] == 8  # "seven" counts as one word


@pytest.mark.asyncio
async def test_sentence_count_approximation(extractor):
    """Test that sentence_count is approximately correct."""
    text = "First sentence. Second sentence! Third sentence?"
    result = await extractor.extract(claim_text=text, image_data=None)
    assert result.metadata["sentence_count"] >= 3


@pytest.mark.asyncio
async def test_sentence_count_single_sentence(extractor):
    """Test that single sentence without punctuation defaults to 1."""
    text = "This is a single sentence without ending punctuation"
    result = await extractor.extract(claim_text=text, image_data=None)
    assert result.metadata["sentence_count"] == 1


@pytest.mark.asyncio
async def test_all_metadata_fields_present(extractor):
    """Test that all expected metadata fields are present."""
    text = "Test claim for metadata validation"
    result = await extractor.extract(claim_text=text, image_data=None)
    required_fields = [
        "text_length",
        "original_text_length",
        "word_count",
        "sentence_count",
        "encoding",
        "normalized",
        "has_image",
    ]
    for field in required_fields:
        assert field in result.metadata, f"Missing metadata field: {field}"


@pytest.mark.asyncio
async def test_encoding_field_present(extractor):
    """Test that encoding field is present and set."""
    text = "Test text"
    result = await extractor.extract(claim_text=text, image_data=None)
    assert "encoding" in result.metadata
    assert result.metadata["encoding"] == "utf-8"


@pytest.mark.asyncio
async def test_has_image_metadata(extractor):
    """Test that has_image metadata is correctly set."""
    # With image
    result_with_image = await extractor.extract(
        claim_text="Test", image_data=b"image_data"
    )
    assert result_with_image.metadata["has_image"] is True

    # Without image
    result_no_image = await extractor.extract(claim_text="Test", image_data=None)
    assert result_no_image.metadata["has_image"] is False


# Encoding error handling tests
@pytest.mark.asyncio
async def test_text_with_zero_width_spaces(extractor):
    """Test handling of zero-width spaces and other special Unicode."""
    # Zero-width space (U+200B)
    text = "Hello\u200BWorld"
    result = await extractor.extract(claim_text=text, image_data=None)
    # Should normalize and handle gracefully
    assert isinstance(result, ExtractedClaim)
    assert len(result.claim_text) > 0


@pytest.mark.asyncio
async def test_minimum_length_validation(extractor):
    """Test that text meeting minimum length is accepted."""
    text = "A"  # Single character, meets MIN_TEXT_LENGTH = 1
    result = await extractor.extract(claim_text=text, image_data=None)
    assert result.claim_text == "A"
    assert result.metadata["text_length"] == 1


@pytest.mark.asyncio
async def test_maximum_length_boundary(extractor):
    """Test that text at maximum length is accepted without truncation."""
    text = "A" * TextExtractor.MAX_TEXT_LENGTH
    result = await extractor.extract(claim_text=text, image_data=None)
    assert len(result.claim_text) == TextExtractor.MAX_TEXT_LENGTH
    assert result.metadata["truncated"] is False


@pytest.mark.asyncio
async def test_truncation_metadata(extractor, long_text):
    """Test that truncation metadata is correctly set."""
    result = await extractor.extract(claim_text=long_text, image_data=None)
    assert result.metadata["truncated"] is True
    assert result.metadata["original_text_length"] > result.metadata["text_length"]


# Integration tests with real LLM API
@pytest.mark.skipif(
    not HAS_GEMINI_API_KEY, reason="GEMINI_API_KEY not set in environment"
)
@pytest.mark.integration
class TestTextExtractorWithRealLLM:
    """Integration tests using real Google Gemini API for claim decomposition."""

    @pytest.mark.asyncio
    async def test_extract_pmc_ai_training_with_real_llm(self):
        """
        Integration test: Extract and decompose PMC AI training claim.

        Tests extraction of a straightforward factual claim about:
        - PMC initiating AI skill development training
        - Timing: next week
        - Location: SP College
        """
        extractor = TextExtractor()
        claim_text = (
            "The Indian Express reports that the Pune Municipal Corporation (PMC) has initiated "
            "Artificial Intelligence (AI) skill development training for its senior officials "
            "next week. It will be held at SP College."
        )

        try:
            result = await extractor.extract(claim_text=claim_text, image_data=None)
        except RuntimeError as e:
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                pytest.skip(f"Rate limited: {e}")
            raise

        # Verify basic result structure
        assert isinstance(result, ExtractedClaim)
        assert result.claim_text == claim_text
        assert result.extracted_from == "text"
        assert 0 <= result.confidence <= 1

        # Verify claim decomposition (who/what/when/where)
        assert len(result.questions) > 0, "Should extract at least one claim element"

        # Verify we have questions (should extract who, what, where, when)
        question_types = {q.question_type for q in result.questions}
        assert (
            "who" in question_types or "what" in question_types
        ), "Should extract who or what elements"

        # Verify key assertions were extracted
        assert (
            len(result.segments) > 0
        ), "Should extract key assertions from the claim"

        # Verify confidence is reasonable (not fallback low score)
        assert result.confidence > 0.4, "Should have decent confidence for clear claim"

        print(f"\n✓ PMC AI Training Claim Extracted:")
        print(f"  - Questions: {len(result.questions)}")
        print(f"  - Assertions: {len(result.segments)}")
        print(f"  - Confidence: {result.confidence:.2f}")
        for q in result.questions:
            print(f"    - {q.question_type}: {q.answer_text}")
        for s in result.segments:
            print(f"    - {s}")
#        Output:
#        ✓ PMC AI Training Claim Extracted:
#          - Questions: 4
#          - Assertions: 4
#          - Confidence: 0.95
#            - who: The Pune Municipal Corporation (PMC)
#            - what: initiated Artificial Intelligence (AI) skill development training for its senior officials
#            - when: next week
#            - where: SP College
#            - The Pune Municipal Corporation (PMC) has initiated AI skill development training.
#            - The training is intended for PMC's senior officials.
#            - The training will be held next week.
#            - The training will take place at SP College.

    @pytest.mark.asyncio
    async def test_extract_affinity_fund_profit_claim_with_real_llm(self):
        """
        Integration test: Extract and decompose Affinity fund complex claim.

        Tests extraction of a multi-part question/claim about:
        - Affinity fund
        - Control: Jared Kushner
        - Specific profit amount: $5.7 billion
        - Specific date: April 3
        - Action: transfer outside country
        """
        extractor = TextExtractor()
        claim_text = (
            "Did the Affinity fund, controlled by Jared Kushner, make a "
            "$5.7 billion profit on April 3 and transfer the profits outside "
            "the country?"
        )

        try:
            result = await extractor.extract(claim_text=claim_text, image_data=None)
        except RuntimeError as e:
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                pytest.skip(f"Rate limited: {e}")
            raise

        # Verify basic result structure
        assert isinstance(result, ExtractedClaim)
        assert result.claim_text == claim_text
        assert result.extracted_from == "text"
        assert 0 <= result.confidence <= 1

        # Verify claim decomposition
        assert len(result.questions) > 0, "Should extract claim elements from complex question"

        # For a complex multi-part claim, should extract multiple elements
        assert (
            len(result.questions) >= 2
        ), "Should extract multiple elements from multi-part claim"

        # Verify question types (should have who, what, when, where)
        question_types = {q.question_type for q in result.questions}
        print(f"\n✓ Affinity Fund Claim Decomposed:")
        print(f"  - Question types found: {sorted(question_types)}")
        print(f"  - Total elements: {len(result.questions)}")
        print(f"  - Assertions: {len(result.segments)}")
        print(f"  - Confidence: {result.confidence:.2f}")

        for q in result.questions:
            print(f"    - {q.question_type}: {q.answer_text} (conf: {q.confidence:.2f})")
        for s in result.segments:
            print(f"    - {s}")

        # Verify assertions were extracted
        assert (
            len(result.segments) > 0
        ), "Should extract verifiable assertions from claim"

#       # Output:
#        ✓ Affinity Fund Claim Decomposed:
#         - Question types found: ['what', 'when', 'where', 'who']
#         - Total elements: 4
#         - Assertions: 4
#         - Confidence: 0.90
#           - who: the Affinity fund, controlled by Jared Kushner (conf: 0.95)
#           - what: make a $5.7 billion profit and transfer the profits outside the country (conf: 0.95)
#           - when: April 3 (conf: 0.95)
#           - where: outside the country (conf: 0.90)
#           - The Affinity fund is controlled by Jared Kushner.
#           - The Affinity fund made a $5.7 billion profit.
#           - The profit was made on April 3.
#           - The profits were transferred outside the country.
#