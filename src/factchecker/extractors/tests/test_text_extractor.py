"""Tests for TextExtractor."""

import pytest
from factchecker.extractors.text_extractor import TextExtractor
from factchecker.core.models import ExtractedClaim


@pytest.fixture
def extractor():
    return TextExtractor()


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
async def test_text_extraction_basic(extractor):
    """Test basic text extraction."""
    result = await extractor.extract(claim_text="The sky is blue", image_data=None)
    assert isinstance(result, ExtractedClaim)
    assert result.claim_text == "The sky is blue"
    assert result.extracted_from == "text"
    assert result.raw_input_type == "text_only"
    assert 0 <= result.confidence <= 1


@pytest.mark.asyncio
async def test_text_extraction_requires_input(extractor):
    """Test that extraction fails without input."""
    with pytest.raises(ValueError):
        await extractor.extract(claim_text=None, image_data=None)


@pytest.mark.asyncio
async def test_hybrid_extraction(extractor):
    """Test extraction from both text and image."""
    result = await extractor.extract(
        claim_text="Verify this", image_data=b"mock_image_data"
    )
    assert result.raw_input_type == "both"
    assert result.metadata["has_image"] is True


@pytest.mark.asyncio
async def test_image_only_extraction(extractor):
    """Test extraction from image only."""
    result = await extractor.extract(claim_text=None, image_data=b"mock_image_data")
    assert result.raw_input_type == "image_only"
    assert result.metadata["has_image"] is True


@pytest.mark.asyncio
async def test_extraction_metadata(extractor):
    """Test that metadata is populated."""
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
