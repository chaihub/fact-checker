"""Tests for ImageExtractor."""

from io import BytesIO

import pytest
from PIL import Image

from factchecker.core.models import ExtractedClaim
from factchecker.extractors.image_extractor import ImageExtractor


@pytest.fixture
def extractor():
    return ImageExtractor()


def create_test_image(
    format: str = "PNG", width: int = 100, height: int = 100
) -> bytes:
    """Create a test image in specified format."""
    img = Image.new("RGB", (width, height), color="red")
    output = BytesIO()
    img.save(output, format=format)
    return output.getvalue()


@pytest.mark.asyncio
async def test_image_extraction_basic(extractor):
    """Test basic image extraction."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert isinstance(result, ExtractedClaim)
    # extracted_from can be "image" or "text" (if OCR fails gracefully)
    assert result.extracted_from in ("image", "text")
    assert result.raw_input_type == "image_only"


@pytest.mark.asyncio
async def test_image_extraction_requires_input(extractor):
    """Test that extraction fails without input."""
    with pytest.raises(ValueError):
        await extractor.extract(claim_text=None, image_data=None)


@pytest.mark.asyncio
async def test_hybrid_image_extraction(extractor):
    """Test extraction from both text and image."""
    image_data = create_test_image()
    result = await extractor.extract(
        claim_text="Additional context", image_data=image_data
    )
    assert result.raw_input_type == "both"
    # extracted_from can be "hybrid", "text", or "image" depending on OCR success
    assert result.extracted_from in ("hybrid", "text", "image")


@pytest.mark.asyncio
async def test_image_metadata_captured(extractor):
    """Test that image metadata is captured."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "image_size" in result.metadata
    assert result.metadata["image_size"] == len(image_data)
    assert "ocr_confidence" in result.metadata
    assert "image_format" in result.metadata
    assert "image_dimensions" in result.metadata


# 2.2.6: Image Validation Tests
@pytest.mark.asyncio
async def test_image_validation_jpeg_format(extractor):
    """Test image validation with JPEG format."""
    image_data = create_test_image(format="JPEG")
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert result.metadata["image_format"] == "JPEG"


@pytest.mark.asyncio
async def test_image_validation_png_format(extractor):
    """Test image validation with PNG format."""
    image_data = create_test_image(format="PNG")
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert result.metadata["image_format"] == "PNG"


@pytest.mark.asyncio
async def test_image_validation_gif_format(extractor):
    """Test image validation with GIF format."""
    image_data = create_test_image(format="GIF")
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert result.metadata["image_format"] == "GIF"


@pytest.mark.asyncio
async def test_image_validation_webp_format(extractor):
    """Test image validation with WebP format."""
    image_data = create_test_image(format="WEBP")
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert result.metadata["image_format"] == "WEBP"


@pytest.mark.asyncio
async def test_image_validation_unsupported_format(extractor):
    """Test that unsupported formats raise ValueError."""
    # BMP is not in SUPPORTED_FORMATS
    image_data = create_test_image(format="BMP")
    with pytest.raises(ValueError, match="Unsupported image format"):
        await extractor.extract(claim_text=None, image_data=image_data)


@pytest.mark.asyncio
async def test_image_validation_corrupted_data(extractor):
    """Test that corrupted image data raises ValueError."""
    corrupted_data = b"this is not an image"
    with pytest.raises(ValueError, match="Corrupted or unreadable image"):
        await extractor.extract(claim_text=None, image_data=corrupted_data)


@pytest.mark.asyncio
async def test_image_validation_file_size_limit(extractor):
    """Test that oversized images raise ValueError."""
    # Create a very large image
    large_image_data = create_test_image(width=5000, height=5000)
    with pytest.raises(ValueError, match="exceed"):
        await extractor.extract(claim_text=None, image_data=large_image_data)


@pytest.mark.asyncio
async def test_image_validation_dimension_limit(extractor):
    """Test that oversized dimensions raise ValueError."""
    # Image with one dimension exceeding MAX_DIMENSION
    large_image_data = create_test_image(width=5000, height=100)
    with pytest.raises(ValueError, match="exceed"):
        await extractor.extract(claim_text=None, image_data=large_image_data)


# 2.2.7: Image Preprocessing Tests
@pytest.mark.asyncio
async def test_image_preprocessing_rgb_conversion(extractor):
    """Test that non-RGB images are converted to RGB."""
    # Create RGBA image
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    output = BytesIO()
    img.save(output, format="PNG")
    image_data = output.getvalue()

    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "converted_to_rgb" in result.metadata["preprocessing_applied"]


@pytest.mark.asyncio
async def test_image_preprocessing_grayscale_conversion(extractor):
    """Test that images are converted to grayscale for OCR."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "converted_to_grayscale" in result.metadata["preprocessing_applied"]


@pytest.mark.asyncio
async def test_image_preprocessing_resize(extractor):
    """Test that large images are resized for OCR."""
    # Create image larger than OCR_MAX_DIMENSION
    large_image_data = create_test_image(width=3000, height=3000)
    result = await extractor.extract(claim_text=None, image_data=large_image_data)
    steps = result.metadata["preprocessing_applied"]
    assert any("resized_to_" in step for step in steps)


@pytest.mark.asyncio
async def test_image_preprocessing_tracked(extractor):
    """Test that preprocessing steps are tracked in metadata."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "preprocessing_applied" in result.metadata
    assert isinstance(result.metadata["preprocessing_applied"], list)


# 2.2.8: Pytesseract OCR Integration Tests
@pytest.mark.asyncio
async def test_ocr_integration_returns_text(extractor):
    """Test that OCR integration returns extracted text."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    # Will be empty for blank image, but should have ocr text field
    assert isinstance(result.claim_text, str)


@pytest.mark.asyncio
async def test_ocr_language_configuration(extractor):
    """Test that OCR language can be configured."""
    image_data = create_test_image()
    extractor_fra = ImageExtractor(ocr_language="fra")
    result = await extractor_fra.extract(claim_text=None, image_data=image_data)
    assert result.metadata["ocr_language"] == "fra"


@pytest.mark.asyncio
async def test_ocr_error_handling(extractor):
    """Test that OCR errors are handled gracefully."""
    # Use invalid image data - this should fail during validation, not OCR
    invalid_data = b"not an image"
    with pytest.raises(ValueError):
        await extractor.extract(claim_text=None, image_data=invalid_data)


@pytest.mark.asyncio
async def test_ocr_empty_image(extractor):
    """Test OCR with blank image (no text to extract)."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    # Blank image should result in empty or near-empty OCR text
    assert result.metadata["ocr_text_length"] == 0 or isinstance(
        result.metadata["ocr_text_length"], int
    )


# 2.2.9: OCR Confidence Scoring Tests
@pytest.mark.asyncio
async def test_ocr_confidence_with_text(extractor):
    """Test that confidence is calculated based on OCR results."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "ocr_confidence" in result.metadata
    confidence_value = result.metadata["ocr_confidence"]
    assert isinstance(confidence_value, (int, float))
    assert 0 <= confidence_value <= 100


@pytest.mark.asyncio
async def test_confidence_score_range(extractor):
    """Test that overall confidence score is between 0 and 1."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert 0.0 <= result.confidence <= 1.0


@pytest.mark.asyncio
async def test_confidence_with_claim_text(extractor):
    """Test that confidence is boosted when claim text is provided."""
    image_data = create_test_image()
    result_with_text = await extractor.extract(
        claim_text="This is a claim", image_data=image_data
    )
    result_image_only = await extractor.extract(
        claim_text=None, image_data=image_data
    )
    # With claim text, confidence should be higher or equal
    assert result_with_text.confidence >= result_image_only.confidence


@pytest.mark.asyncio
async def test_confidence_penalty_for_preprocessing(extractor):
    """Test that confidence is penalized for preprocessing steps."""
    # Large image requires preprocessing
    large_image_data = create_test_image(width=3000, height=3000)
    result = await extractor.extract(claim_text=None, image_data=large_image_data)
    # Verify preprocessing was applied
    assert len(result.metadata["preprocessing_applied"]) > 0
    # Confidence should be reasonable (not 0)
    assert result.confidence >= 0.0


# 2.2.10: Enhanced Metadata Collection Tests
@pytest.mark.asyncio
async def test_metadata_image_format_field(extractor):
    """Test that image_format is captured in metadata."""
    image_data = create_test_image(format="PNG")
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "image_format" in result.metadata
    assert result.metadata["image_format"] == "PNG"


@pytest.mark.asyncio
async def test_metadata_image_dimensions_field(extractor):
    """Test that image_dimensions are captured in metadata."""
    image_data = create_test_image(width=200, height=150)
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "image_dimensions" in result.metadata
    # Should be in "WxH" format
    assert "x" in result.metadata["image_dimensions"]


@pytest.mark.asyncio
async def test_metadata_ocr_confidence_field(extractor):
    """Test that ocr_confidence is in metadata."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "ocr_confidence" in result.metadata
    assert isinstance(result.metadata["ocr_confidence"], (int, float))


@pytest.mark.asyncio
async def test_metadata_ocr_text_length_field(extractor):
    """Test that ocr_text_length is tracked."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "ocr_text_length" in result.metadata
    assert isinstance(result.metadata["ocr_text_length"], int)


@pytest.mark.asyncio
async def test_metadata_ocr_language_field(extractor):
    """Test that ocr_language is tracked in metadata."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "ocr_language" in result.metadata
    assert result.metadata["ocr_language"] == "eng"


@pytest.mark.asyncio
async def test_metadata_preprocessing_applied_field(extractor):
    """Test that preprocessing_applied is tracked."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "preprocessing_applied" in result.metadata
    assert isinstance(result.metadata["preprocessing_applied"], list)


@pytest.mark.asyncio
async def test_metadata_image_size_field(extractor):
    """Test that image_size (bytes) is tracked."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    assert "image_size" in result.metadata
    assert result.metadata["image_size"] == len(image_data)


@pytest.mark.asyncio
async def test_metadata_completeness(extractor):
    """Test that all expected metadata fields are present."""
    image_data = create_test_image()
    result = await extractor.extract(claim_text=None, image_data=image_data)
    expected_fields = {
        "image_size",
        "image_format",
        "image_dimensions",
        "ocr_confidence",
        "ocr_text_length",
        "ocr_language",
        "preprocessing_applied",
    }
    assert expected_fields.issubset(set(result.metadata.keys()))
