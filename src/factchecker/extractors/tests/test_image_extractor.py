"""Tests for ImageExtractor."""

import pytest
from factchecker.extractors.image_extractor import ImageExtractor
from factchecker.core.models import ExtractedClaim


@pytest.fixture
def extractor():
    return ImageExtractor()


@pytest.mark.asyncio
async def test_image_extraction_basic(extractor):
    """Test basic image extraction."""
    result = await extractor.extract(
        claim_text=None, image_data=b"mock_image_data"
    )
    assert isinstance(result, ExtractedClaim)
    assert result.extracted_from == "image"
    assert result.raw_input_type == "image_only"


@pytest.mark.asyncio
async def test_image_extraction_requires_input(extractor):
    """Test that extraction fails without input."""
    with pytest.raises(ValueError):
        await extractor.extract(claim_text=None, image_data=None)


@pytest.mark.asyncio
async def test_hybrid_image_extraction(extractor):
    """Test extraction from both text and image."""
    result = await extractor.extract(
        claim_text="Additional context", image_data=b"mock_image_data"
    )
    assert result.raw_input_type == "both"
    assert result.extracted_from == "image"


@pytest.mark.asyncio
async def test_image_metadata_captured(extractor):
    """Test that image metadata is captured."""
    image_data = b"mock_image_with_size"
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "image_size" in result.metadata
    assert result.metadata["image_size"] == len(image_data)
    assert "ocr_confidence" in result.metadata
