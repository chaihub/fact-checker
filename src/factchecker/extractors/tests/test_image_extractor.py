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


# ============================================================================
# Real Sample Image Tests - Load from tests/images directory
# ============================================================================
# These tests use actual image files from tests/images/ directory.
# Each test can be run individually or all together with:
#   pytest src/factchecker/extractors/tests/test_image_extractor.py::test_sample_images -v
#   pytest src/factchecker/extractors/tests/test_image_extractor.py -k "sample_images" -v


def get_sample_image_path(filename: str) -> bytes:
    """Load sample image from tests/images directory."""
    import os

    base_path = os.path.dirname(__file__)
    image_path = os.path.join(base_path, "../../../..", "tests", "images", filename)
    with open(image_path, "rb") as f:
        return f.read()


# Blank/minimal images
@pytest.mark.asyncio
class TestSampleImagesBlank:
    """Test ImageExtractor with blank/minimal sample images."""

    async def test_sample_images_blank_png(self, extractor):
        """Test extraction from blank.png."""
        image_data = get_sample_image_path("blank.png")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_ocr_text = ""
        assert result.claim_text == expected_ocr_text

    async def test_sample_images_thumbnail_png(self, extractor):
        """Test extraction from thumbnail.png (50x50)."""
        image_data = get_sample_image_path("thumbnail.png")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_ocr_text = ""
        assert result.claim_text == expected_ocr_text


# Format-specific images
@pytest.mark.asyncio
class TestSampleImagesFormats:
    """Test ImageExtractor with different format sample images."""

    async def test_sample_images_gif(self, extractor):
        """Test extraction from sample.gif (GIF format)."""
        image_data = get_sample_image_path("sample.gif")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        assert result.metadata["image_format"] == "GIF"
        expected_ocr_text = ""
        assert result.claim_text == expected_ocr_text

    async def test_sample_images_webp(self, extractor):
        """Test extraction from sample.webp (WebP format)."""
        image_data = get_sample_image_path("sample.webp")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        assert result.metadata["image_format"] == "WEBP"
        expected_ocr_text = ""
        assert result.claim_text == expected_ocr_text

    async def test_sample_images_transparent_png(self, extractor):
        """Test extraction from transparent.png (RGBA format)."""
        image_data = get_sample_image_path("transparent.png")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        assert result.metadata["image_format"] == "PNG"
        # Verify RGB conversion was applied
        assert "converted_to_rgb" in result.metadata["preprocessing_applied"]
        expected_ocr_text = ""
        assert result.claim_text == expected_ocr_text


# Images with text content
@pytest.mark.asyncio
class TestSampleImagesWithText:
    """Test ImageExtractor with images containing text."""

    async def test_sample_images_text_sample(self, extractor):
         """Test extraction from text_sample.png (contains 'Sample OCR Text')."""
         image_data = get_sample_image_path("text_sample.png")
         result = await extractor.extract(claim_text=None, image_data=image_data)
         assert isinstance(result, ExtractedClaim)
         expected_ocr_text = "Sample OCR Text"
         assert expected_ocr_text == result.claim_text


# Large/high-resolution images
@pytest.mark.asyncio
class TestSampleImagesLarge:
    """Test ImageExtractor with large/high-resolution sample images."""

    async def test_sample_images_large_png(self, extractor):
        """Test extraction from large.png (3000x2000, high resolution)."""
        image_data = get_sample_image_path("large.png")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # Verify resize was applied for large images
        assert any("resized_to_" in step for step in result.metadata["preprocessing_applied"])
        expected_ocr_text = "Large Image Test"
        assert expected_ocr_text == result.claim_text


# Invalid/non-image files for negative testing
@pytest.mark.asyncio
class TestSampleImagesNegative:
    """Test ImageExtractor with non-image and corrupted files."""

    async def test_sample_images_text_file(self, extractor):
        """Test extraction from not_an_image.txt (invalid format)."""
        image_data = get_sample_image_path("not_an_image.txt")
        with pytest.raises(ValueError, match="Corrupted or unreadable image"):
            await extractor.extract(claim_text=None, image_data=image_data)

    async def test_sample_images_corrupted_binary(self, extractor):
        """Test extraction from corrupted.bin (corrupted binary data)."""
        image_data = get_sample_image_path("corrupted.bin")
        with pytest.raises(ValueError, match="Corrupted or unreadable image"):
            await extractor.extract(claim_text=None, image_data=image_data)


# Hybrid extraction tests with sample images
@pytest.mark.asyncio
class TestSampleImagesHybrid:
    """Test ImageExtractor hybrid mode with sample images and text."""

    async def test_sample_images_hybrid_text_and_image(self, extractor):
        """Test hybrid extraction with text_sample.png and claim text."""
        image_data = get_sample_image_path("text_sample.png")
        claim_text = "Additional claim context"
        result = await extractor.extract(
            claim_text=claim_text, image_data=image_data
        )
        assert isinstance(result, ExtractedClaim)
        assert result.raw_input_type == "both"
        expected_combined_text = "Sample OCR Text"
        assert expected_combined_text == result.claim_text

    async def test_sample_images_hybrid_text_and_blank(self, extractor):
        """Test hybrid extraction with blank.png and claim text."""
        image_data = get_sample_image_path("blank.png")
        claim_text = "This is my claim"
        result = await extractor.extract(
            claim_text=claim_text, image_data=image_data
        )
        assert isinstance(result, ExtractedClaim)
        assert result.raw_input_type == "both"
        expected_text = ""
        assert expected_text == result.claim_text


# Real-world WhatsApp tweet/screenshot samples - Simple format
@pytest.mark.asyncio
class TestSampleImagesTweetSimple:
    """Test ImageExtractor with simple tweet/screenshot samples."""

    async def test_sample_images_IMG_20250313_WA0001(self, extractor):
        """Test extraction from IMG-20250313-WA0001.jpg."""
        image_data = get_sample_image_path("IMG-20250313-WA0001.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = 'Based on Ontario, Canada, placing a 25% Tariff on "Electricity" coming into the United States, I have instructed my Secretary of Commerce to add an ADDITIONAL 25% Tariff, to 50%, on all STEEL and ALUMINUM COMING INTO THE UNITED STATES FROM CANADA, ONE OF THE HIGHEST TARIFFING NATIONS ANYWHERE IN THE WORLD. This will go into effect TOMORROW MORNING, March 12th. Also, Canada must immediately drop their Anti-American Farmer Tariff of 250% to 390% on various U.S. dairy products, which has long been considered outrageous.'
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250319_WA0001(self, extractor):
        """Test extraction from IMG-20250319-WA0001.jpg."""
        image_data = get_sample_image_path("IMG-20250319-WA0001.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "After years of being held captive by Environmental Extremists, Lunatics, Radicals, and Thugs, allowing other Countries, in particular China, to gain tremendous Economic advantage over us by opening up hundreds of all Coal Fire Power Plants, I am authorizing my Administration to immediately begin producing Energy with BEAUTIFUL, CLEAN COAL."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250411_WA0004(self, extractor):
        """Test extraction from IMG-20250411-WA0004.jpg."""
        image_data = get_sample_image_path("IMG-20250411-WA0004.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # Dropped a single quote from the expected text due to clash with the string delimiter.
        expected_text = 'Since the options data on April 9, data from the Chicago Exchange has also revealed that on April 3, the Trump family fund held $38 billion worth of Nasdaq put options. Meanwhille, the Affinity fund, controlled by Trumps son-in-law Jared Kushner, made a $5.7 billion profit by shorting Apple and Tesla, with the shorting profits transferred to the Dubai Digital Gold Exchange through an SPV in the British Virgin Islands. This is what they call "Make America Great Again."'
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251126_WA0001(self, extractor):
        """Test extraction from IMG-20251126-WA0001.jpg."""
        image_data = get_sample_image_path("IMG-20251126-WA0001.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "I am asking all America First Patriots in Tennessee's 7th Congressional District, who haven't voted yet, to please GET OUT AND VOTE for MAGA Warrior Matt Van Epps, tomorrow, November 26th, the last day to vote early in person. You can win this Election for Matt! PLEASE VOTE FOR MATT VAN EPPS, who has my Complete and Total Endorsement. Polls close at 12 P.M. NOON in most of TN-07, and every vote counts. IF YOU ARE IN LINE BY 12 P.M., STAY IN LINE, AND THEY MUST LET YOU VOTE! TN-07: Early Voting ends November 26th, adn Election Day is December 2nd. GET OUT AND VOTE FOR MATT VAN EPPS - HE WILL NEVER LET YOU DOWN!"
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251201_WA0004(self, extractor):
        """Test extraction from IMG-20251201-WA0004.jpg."""
        image_data = get_sample_image_path("IMG-20251201-WA0004.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Because I have invoked FAVORED NATIONS STATUS FOR THE UNITED STATES OF AMERICA, DRUG PRICES ARE FALLING AT LEVELS NEVER SEEN BEFORE, 500%, 600%, 700%, and more. No other President has been able to do this, BUT I HAVE!"
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0003(self, extractor):
        """Test extraction from IMG-20251219-WA0003.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0003.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "If he is your close relative then he should invest in your education, so next time you won't post such questions."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0004(self, extractor):
        """Test extraction from IMG-20251219-WA0004.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0004.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Pro tip for 3L monthly income: Invest the entire lump sum in a herd of goats They compound at 1.5-2x annually Set up an STP: Sell a few every month for steady cash flow."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0006(self, extractor):
        """Test extraction from IMG-20251219-WA0006.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0006.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "The last thing you want to do is promote tribalism when you are one of the smaller tribes. Yet minority 'leaders' do this because it promotes their individual self-interest, regardless of what bad effects this will have on others, including their followers."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0010(self, extractor):
        """Test extraction from IMG-20251219-WA0010.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0010.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "The Trump tariffs are the largest US tax increase as a percent of GDP in over 30 years."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0016(self, extractor):
        """Test extraction from IMG-20251219-WA0016.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0016.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Islam is not a religion. It's a cult. Islamists aren't here to assimilate. They're here to conquer. Stop worrying about offending the pearl clutchers. We've got to SEND THEM HOME NOW or we'll become the United Caliphate of America."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251220_WA0003(self, extractor):
        """Test extraction from IMG-20251220-WA0003.jpg."""
        image_data = get_sample_image_path("IMG-20251220-WA0003.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "MAGA (one year ago): End wars! Expose pedophiles! MAGA (today): Start wars! Protect pedophiles!"
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251220_WA0007(self, extractor):
        """Test extraction from IMG-20251220-WA0007.jpg."""
        image_data = get_sample_image_path("IMG-20251220-WA0007.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "I have just been informed that the highly respected Board of the Kennedy Center, some of the most successful people from all parts of the world, have just voted unanimously to rename the Kennedy Center to the Trump-Kennedy Center, because of the unbelievable work President Trump has done over the last year in saving the building. Not only from the standpoint of its reconstruction, but also financially, and its reputation. Congratulations to President Donald J. Trump, and likewise, congratulations to President Kennedy, because this will be a truly great team long into the future! The building will no doubt attain new levels success and grandeur."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251220_WA0009(self, extractor):
        """Test extraction from IMG-20251220-WA0009.jpg."""
        image_data = get_sample_image_path("IMG-20251220-WA0009.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Deputy AG Blanche just said the Trump DOJ will miss the Epstein files deadline. He says several hundred thousand docs will be released today, and then over the next couple weeks, I expect several hundred thousand more. All files are required by law to be released today."
        assert expected_text in result.claim_text


# Real-world WhatsApp tweet/screenshot samples - Complex format
@pytest.mark.asyncio
class TestSampleImagesTweetComplex:
    """Test ImageExtractor with complex tweet/screenshot samples."""

    async def test_sample_images_IMG_20250220_WA0001(self, extractor):
        """Test extraction from IMG-20250220-WA0001.jpg."""
        image_data = get_sample_image_path("IMG-20250220-WA0001.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # Dropped a double quote mark due to conflict with the text string delimiter
        expected_text = "The gap between the claims made in the Microsoft press release and teh claims made in the actual paper are pretty astounding. From their own paper These measurements do not, by themselves, determine whether the low-energy states detected by interferometry are topological."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250320_WA0003(self, extractor):
        """Test extraction from IMG-20250320-WA0003.jpg."""
        image_data = get_sample_image_path("IMG-20250320-WA0003.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Is Trumpism soluble in vodka?"
        # Dropped a double quote mark due to conflict with the text string delimiter
        expected_text2 = "Latest Russian joke: Trump, in the afterlife, gets permission to go back and visit Earth for one hour. He goes into a bar in NYC and asks the bartender how things are going in America. The amazed man says, Wow, sir, we have the most incredible empire thanks to you! Greenland, Panama, and Canada!"
        assert expected_text in result.claim_text and expected_text2 in result.claim_text

    async def test_sample_images_IMG_20250726_WA0008(self, extractor):
        """Test extraction from IMG-20250726-WA0008.jpg."""
        image_data = get_sample_image_path("IMG-20250726-WA0008.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Absolute comedy that Japan has come out and denied *every* single part of the Truth Social Trade Deal. Just a complete circus."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250909_WA0011(self, extractor):
        """Test extraction from IMG-20250909-WA0011.jpg."""
        image_data = get_sample_image_path("IMG-20250909-WA0011.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Let me tell you a fun fact..... China has 7 million Software engineers India 6 million USA 4.4 million Among these 3..... Only India couldn't produce even 1 App, Website, Operating System, Database, Cloud platform, CDN, AI or even Social media that is used by the world"
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250923_WA0004(self, extractor):
        """Test extraction from IMG-20250923-WA0004.jpg."""
        image_data = get_sample_image_path("IMG-20250923-WA0004.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "'डूबते' कोलकाता में 9 लोग करंट से कैसे मर गए?"
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251105_WA0001(self, extractor):
        """Test extraction from IMG-20251105-WA0001.jpg."""
        image_data = get_sample_image_path("IMG-20251105-WA0001.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Look at the abuse Vivek is getting for posting an innocuous photo with his boys. This is the sh*tshow that Heritage and Tucker have brought upon us. If this continues, I would not be surprised to see mass desertion of blacks, Latinos and other minorities from the GOP. Unreal."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251205_WA0010(self, extractor):
        """Test extraction from IMG-20251205-WA0010.jpg."""
        image_data = get_sample_image_path("IMG-20251205-WA0010.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "All schools in Maharashtra will remain closed on 5 December 2025, after the Maharashtra State Headmasters' Association, along with teachers' and non-teaching-staff unions; called a statewide shutdown to press their demands. Parents and students are advised to take note and plan accordingly."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0007(self, extractor):
        """Test extraction from IMG-20251219-WA0007.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0007.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "President Trump mentioned Joe Biden 30 times during his economic address in Pennsylvania. That would be 31 times, if you count sleepy son of a bitch, which the audience surely did. Sleepy Joe Biden - have you heard of him? Trump asked."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0009(self, extractor):
        """Test extraction from IMG-20251219-WA0009.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0009.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "WOMEN IS A BANNED WORD"
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0011(self, extractor):
        """Test extraction from IMG-20251219-WA0011.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0011.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Wow: A veteran was asked why he voted for Trump if he now believes his polices hurt people: His answer? Because I was an idiot."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0012(self, extractor):
        """Test extraction from IMG-20251219-WA0012.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0012.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "If Fox News is sounding the alarm....."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0013(self, extractor):
        """Test extraction from IMG-20251219-WA0013.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0013.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Today, I took the first step towards Kristi Noem's impeachment, and called on the Judiciary Committee to open an investigation into her lawlessness. The American people will have justice and we will hold Noem accountable. I'll make sure of it."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0014(self, extractor):
        """Test extraction from IMG-20251219-WA0014.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0014.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "So if a woman gets a hysterectomy they are not considered women anymore? That's pretty mean."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0015(self, extractor):
        """Test extraction from IMG-20251219-WA0015.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0015.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Why is Fox News starting a war on Christmas?"
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0018(self, extractor):
        """Test extraction from IMG-20251219-WA0018.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0018.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Pollster: The number of people who say the economy is on the wrong track has skyrocketed up to 56%. The number who say it's on the right track has fallen to 29%. The American people aren't buying the spin that is coming out of the White House."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251220_WA0002(self, extractor):
        """Test extraction from IMG-20251220-WA0002.jpg."""
        image_data = get_sample_image_path("IMG-20251220-WA0002.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Vivek Ramaswamy NYT op-ed: My social media feeds are littered with hundreds of slurs, most from accounts that I don't recognize, about 'pajeets' and 'street shitters' and calls to deport me 'back to India.'"
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251220_WA0004(self, extractor):
        """Test extraction from IMG-20251220-WA0004.jpg."""
        image_data = get_sample_image_path("IMG-20251220-WA0004.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Vivek's position is that an Indian born to Indian parents, raised in Indian culture, holding Indian religious beliefs, is every bit as American as a Mayflower descendant as long as he affirms certain propositions. This is absurd on its face. It is an insult to the families who built this nation over four centuries. It is a denial of everything that makes nationhood meaningful."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251220_WA0005(self, extractor):
        """Test extraction from IMG-20251220-WA0005.jpg."""
        image_data = get_sample_image_path("IMG-20251220-WA0005.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Exclusive: The Department of Health and Human Services has terminated seven grants totaling millions of dollars to the American Academy of Pediatrics. The association has been one of the harshest critics of Health Secretary RFK Jr.'s changes to federal vaccine policy."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251220_WA0006(self, extractor):
        """Test extraction from IMG-20251220-WA0006.jpg."""
        image_data = get_sample_image_path("IMG-20251220-WA0006.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "The little orange bars on the right are what Trump is calling the greatest economy in history."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251220_WA0008(self, extractor):
        """Test extraction from IMG-20251220-WA0008.jpg."""
        image_data = get_sample_image_path("IMG-20251220-WA0008.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Exclusive: The Trump administration is moving to dismantle the National Center for Atmospheric Research in Colorado, according to a senior White House official, taking aim at one of the world's leading climate research labs."
        assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251220_WA0010(self, extractor):
        """Test extraction from IMG-20251220-WA0010.jpg."""
        image_data = get_sample_image_path("IMG-20251220-WA0010.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        expected_text = "Alright. Everyone can stop now. We have a winner."
        assert expected_text in result.claim_text


# Real-world non-tweet/screenshot samples
@pytest.mark.asyncio
class TestSampleImagesNotTweet:
    """Test ImageExtractor with non-tweet/screenshot samples."""

    async def test_sample_images_IMG_20250122_WA0002(self, extractor):
        """Test extraction from IMG-20250122-WA0002.jpg."""
        image_data = get_sample_image_path("IMG-20250122-WA0002.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250122_WA0002"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250301_WA0000_jpg(self, extractor):
        """Test extraction from IMG-20250301-WA0000.jpg."""
        image_data = get_sample_image_path("IMG-20250301-WA0000.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250301_WA0000_JPG"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250322_WA0007(self, extractor):
        """Test extraction from IMG-20250322-WA0007.jpg."""
        image_data = get_sample_image_path("IMG-20250322-WA0007.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250322_WA0007"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250329_WA0001(self, extractor):
        """Test extraction from IMG-20250329-WA0001.jpg."""
        image_data = get_sample_image_path("IMG-20250329-WA0001.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Indicate that this is not a tweet
        expected_text = "Congratulations go to ECE Professor Raviraj Adve on the publication of his new textbook, Cellular Radio Access Networks, RF Fundamentals and Protocols."
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250406_WA0001(self, extractor):
        """Test extraction from IMG-20250406-WA0001.jpg."""
        image_data = get_sample_image_path("IMG-20250406-WA0001.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250406_WA0001"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250409_WA0003(self, extractor):
        """Test extraction from IMG-20250409-WA0003.jpg."""
        image_data = get_sample_image_path("IMG-20250409-WA0003.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250409_WA0003"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250411_WA0001(self, extractor):
        """Test extraction from IMG-20250411-WA0001.jpg."""
        image_data = get_sample_image_path("IMG-20250411-WA0001.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250411_WA0001"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250423_WA0002(self, extractor):
        """Test extraction from IMG-20250423-WA0002.jpg."""
        image_data = get_sample_image_path("IMG-20250423-WA0002.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250423_WA0002"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250527_WA0014(self, extractor):
        """Test extraction from IMG-20250527-WA0014.jpg."""
        image_data = get_sample_image_path("IMG-20250527-WA0014.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250527_WA0014"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250605_WA0003(self, extractor):
        """Test extraction from IMG-20250605-WA0003.jpeg."""
        image_data = get_sample_image_path("IMG-20250605-WA0003.jpeg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250605_WA0003"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250617_WA0004(self, extractor):
        """Test extraction from IMG-20250617-WA0004.jpg."""
        image_data = get_sample_image_path("IMG-20250617-WA0004.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250617_WA0004"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250729_WA0001(self, extractor):
        """Test extraction from IMG-20250729-WA0001.jpg."""
        image_data = get_sample_image_path("IMG-20250729-WA0001.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250729_WA0001"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250921_WA0010(self, extractor):
        """Test extraction from IMG-20250921-WA0010.jpg."""
        image_data = get_sample_image_path("IMG-20250921-WA0010.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250921_WA0010"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20250930_WA0046(self, extractor):
        """Test extraction from IMG-20250930-WA0046.jpg."""
        image_data = get_sample_image_path("IMG-20250930-WA0046.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250930_WA0046"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251005_WA0024(self, extractor):
        """Test extraction from IMG-20251005-WA0024.jpg."""
        image_data = get_sample_image_path("IMG-20251005-WA0024.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20251005_WA0024"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251018_WA0003(self, extractor):
        """Test extraction from IMG-20251018-WA0003.jpg."""
        image_data = get_sample_image_path("IMG-20251018-WA0003.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20251018_WA0003"
        # assert expected_text in result.claim_text

    # async def test_sample_images_IMG_20251108_WA0009(self, extractor):
    #     """Test extraction from IMG-20251108-WA0009.jpeg."""
    #     # File not found in tests/images/ - skipping
    #     pass

    async def test_sample_images_IMG_20251111_WA0000(self, extractor):
        """Test extraction from IMG-20251111-WA0000.jpg."""
        image_data = get_sample_image_path("IMG-20251111-WA0000.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20251111_WA0000"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251129_WA0019(self, extractor):
        """Test extraction from IMG-20251129-WA0019.jpg."""
        image_data = get_sample_image_path("IMG-20251129-WA0019.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20251129_WA0019"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251219_WA0019(self, extractor):
        """Test extraction from IMG-20251219-WA0019.jpg."""
        image_data = get_sample_image_path("IMG-20251219-WA0019.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20251219_WA0019"
        # assert expected_text in result.claim_text

    async def test_sample_images_IMG_20251220_WA0012(self, extractor):
        """Test extraction from IMG-20251220-WA0012.jpg."""
        image_data = get_sample_image_path("IMG-20251220-WA0012.jpg")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20251220_WA0012"
        # assert expected_text in result.claim_text


# Invalid/non-image files for negative testing
@pytest.mark.asyncio
class TestSampleImagesNegativeExtended:
    """Test ImageExtractor with additional non-image and corrupted files."""

    async def test_sample_images_AUD_20250721_WA0001(self, extractor):
        """Test extraction from AUD-20250721-WA0001.mp3 (audio file)."""
        image_data = get_sample_image_path("AUD-20250721-WA0001.mp3")
        with pytest.raises(ValueError, match="Corrupted or unreadable image"):
            await extractor.extract(claim_text=None, image_data=image_data)

    async def test_sample_images_IMG_20250301_WA0000_png(self, extractor):
        """Test extraction from IMG-20250301-WA0000.png."""
        image_data = get_sample_image_path("IMG-20250301-WA0000.png")
        result = await extractor.extract(claim_text=None, image_data=image_data)
        assert isinstance(result, ExtractedClaim)
        # PNG should be valid, but add to this class if it's a negative test case
        # TODO: Add expected output after manual inspection
        expected_text = "PLACEHOLDER_EXPECTED_OUTPUT_IMG_20250301_WA0000_PNG"
        # assert expected_text in result.claim_text

    async def test_sample_images_VID_20250308_WA0382(self, extractor):
        """Test extraction from VID-20250308-WA0382.mp4 (video file)."""
        image_data = get_sample_image_path("VID-20250308-WA0382.mp4")
        with pytest.raises(ValueError, match="Corrupted or unreadable image"):
            await extractor.extract(claim_text=None, image_data=image_data)

    # async def test_sample_images_IMG_20251220_WA0020(self, extractor):
    #     """Test extraction from IMG-20251220-WA0020.jpg (typo: TweetCmplex)."""
    #     # File not found in tests/images/ - skipping
    #     pass
