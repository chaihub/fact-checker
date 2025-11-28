"""Tests for TextExtractor."""

import pytest
from factchecker.extractors.text_extractor import TextExtractor
from factchecker.core.models import ExtractedClaim


@pytest.fixture
def extractor():
    return TextExtractor()


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
