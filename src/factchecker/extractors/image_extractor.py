"""Image-based claim extractor with OCR."""

from __future__ import annotations

from io import BytesIO
from typing import Optional

import pytesseract
from PIL import Image, UnidentifiedImageError

from factchecker.core.interfaces import BaseExtractor
from factchecker.core.models import ExtractedClaim
from factchecker.logging_config import get_logger

from factchecker.debug_utils import dump_image_debug

logger = get_logger(__name__)

SUPPORTED_FORMATS: frozenset[str] = frozenset({"JPEG", "PNG", "GIF", "WEBP"})
MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
MAX_DIMENSION: int = 4096  # pixels
OCR_MAX_DIMENSION: int = 2048  # resize to this before OCR to prevent timeout
DEFAULT_OCR_LANGUAGE: str = "eng"


class ImageExtractor(BaseExtractor):
    """Extracts claims from image input using OCR."""

    def __init__(
        self,
        ocr_language: str = DEFAULT_OCR_LANGUAGE,
        convert_to_grayscale: bool = True,
    ) -> None:
        self.ocr_language = ocr_language
        self.convert_to_grayscale = convert_to_grayscale

    async def extract(
        self, claim_text: Optional[str], image_data: Optional[bytes]
    ) -> ExtractedClaim:
        """Extract structured claim from image via OCR."""
        if not claim_text and not image_data:
            raise ValueError(
                "At least one of claim_text or image_data must be provided"
            )

        if claim_text and image_data:
            raw_input_type = "both"
        elif image_data:
            raw_input_type = "image_only"
        else:
            raw_input_type = "text_only"

        metadata: dict[str, object] = {}
        ocr_text = ""
        ocr_confidence = 0.0
        preprocessing_applied: list[str] = []

        if image_data:
            metadata["image_size"] = len(image_data)

            image = self._validate_image(image_data)
            metadata["image_format"] = image.format
            metadata["image_dimensions"] = f"{image.width}x{image.height}"

            image, preprocessing_applied = self._preprocess_image(image)
            metadata["preprocessing_applied"] = preprocessing_applied

            ocr_text, ocr_confidence = self._perform_ocr(image)
            metadata["ocr_text_length"] = len(ocr_text)
            metadata["ocr_confidence"] = ocr_confidence
            metadata["ocr_language"] = self.ocr_language

        if claim_text and ocr_text:
            extracted_text = f"{claim_text}\n\n[OCR]: {ocr_text}"
            extracted_from = "hybrid"
        elif ocr_text:
            extracted_text = ocr_text
            extracted_from = "image"
        else:
            extracted_text = claim_text or ""
            extracted_from = "text"

        final_confidence = self._calculate_confidence(
            ocr_confidence=ocr_confidence,
            has_ocr_text=bool(ocr_text),
            has_claim_text=bool(claim_text),
            preprocessing_steps=len(preprocessing_applied),
        )

        return ExtractedClaim(
            claim_text=extracted_text,
            extracted_from=extracted_from,
            confidence=final_confidence,
            raw_input_type=raw_input_type,
            metadata=metadata,
        )

    def _validate_image(self, image_data: bytes) -> Image.Image:
        """Validate image format, size, and integrity.

        Args:
            image_data: Raw image bytes.

        Returns:
            PIL Image object if valid.

        Raises:
            ValueError: If image is corrupted, too large, or unsupported format.
        """
        if len(image_data) > MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"Image file size ({len(image_data)} bytes) exceeds "
                f"maximum allowed ({MAX_FILE_SIZE_BYTES} bytes)"
            )

        try:
            image = Image.open(BytesIO(image_data))
            image.verify()
            image = Image.open(BytesIO(image_data))
        except UnidentifiedImageError as e:
            raise ValueError(f"Corrupted or unreadable image: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to open image: {e}") from e

        detected_format = image.format
        if detected_format not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported image format '{detected_format}'. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
            )

        if image.width > MAX_DIMENSION or image.height > MAX_DIMENSION:
            raise ValueError(
                f"Image dimensions ({image.width}x{image.height}) exceed "
                f"maximum allowed ({MAX_DIMENSION}x{MAX_DIMENSION})"
            )

        logger.debug(
            f"Image validated: format={detected_format}, "
            f"size={image.width}x{image.height}"
        )
        return image

    def _preprocess_image(
        self, image: Image.Image
    ) -> tuple[Image.Image, list[str]]:
        """Preprocess image for OCR.

        Args:
            image: PIL Image object.

        Returns:
            Tuple of (processed image, list of preprocessing steps applied).
        """
        steps: list[str] = []

        if image.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            if image.mode in ("RGBA", "LA"):
                background.paste(image, mask=image.split()[-1])
                image = background
            else:
                image = image.convert("RGB")
            steps.append("converted_to_rgb")
        elif image.mode != "RGB" and image.mode != "L":
            image = image.convert("RGB")
            steps.append("converted_to_rgb")

        max_dim = max(image.width, image.height)
        if max_dim > OCR_MAX_DIMENSION:
            ratio = OCR_MAX_DIMENSION / max_dim
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            steps.append(f"resized_to_{new_width}x{new_height}")
            logger.debug(f"Image resized from {max_dim}px to {OCR_MAX_DIMENSION}px")

        if self.convert_to_grayscale and image.mode != "L":
            image = image.convert("L")
            steps.append("converted_to_grayscale")

        dump_image_debug(image, "after_preprocessing")

        return image, steps

    def _perform_ocr(self, image: Image.Image) -> tuple[str, float]:
        """Perform OCR on image using pytesseract.

        Args:
            image: Preprocessed PIL Image.

        Returns:
            Tuple of (extracted text, confidence score 0-100).
        """
        try:
            ocr_data = pytesseract.image_to_data(
                image, lang=self.ocr_language, output_type=pytesseract.Output.DICT
            )

            confidences = [
                int(conf)
                for conf, text in zip(ocr_data["conf"], ocr_data["text"])
                if int(conf) >= 0 and text.strip()
            ]

            text_parts = [
                text
                for conf, text in zip(ocr_data["conf"], ocr_data["text"])
                if int(conf) >= 0 and text.strip()
            ]
            extracted_text = " ".join(text_parts).strip()

            if confidences:
                mean_confidence = sum(confidences) / len(confidences)
            else:
                mean_confidence = 0.0

            logger.debug(
                f"OCR completed: {len(extracted_text)} chars, "
                f"confidence={mean_confidence:.1f}"
            )
            return extracted_text, mean_confidence

        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            return "", 0.0

    def _calculate_confidence(
        self,
        ocr_confidence: float,
        has_ocr_text: bool,
        has_claim_text: bool,
        preprocessing_steps: int,
    ) -> float:
        """Calculate overall extraction confidence.

        Args:
            ocr_confidence: OCR confidence score (0-100).
            has_ocr_text: Whether OCR extracted any text.
            has_claim_text: Whether claim text was provided.
            preprocessing_steps: Number of preprocessing steps applied.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if has_claim_text and not has_ocr_text:
            return 1.0

        if not has_ocr_text:
            return 0.1

        base_confidence = ocr_confidence / 100.0

        preprocessing_penalty = min(preprocessing_steps * 0.02, 0.1)
        base_confidence -= preprocessing_penalty

        if has_claim_text:
            base_confidence = min(base_confidence + 0.1, 1.0)

        return max(0.0, min(1.0, base_confidence))
