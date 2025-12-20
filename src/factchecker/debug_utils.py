"""Debug utilities for development and troubleshooting.

Usage:
    from factchecker.debug_utils import dump_image_debug
    dump_image_debug(image, "stage_name")  # Call anytime while debugging
    
Enable image dumping:
    export FACTCHECKER_DEBUG_IMAGES=1
    pytest src/factchecker/extractors/tests/test_image_extractor.py -xvs
    
Output:
    Images saved to .debug_images/ with timestamp_stagename.png
    Add .debug_images/ to .gitignore (already configured)
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from PIL.Image import Image


DEBUG_DIR = Path(".debug_images")


def dump_image_debug(image: Image, name: str) -> None:
    """Save image to debug directory if debugging is enabled.

    Call this function at any point while debugging to inspect image state.
    No-op if FACTCHECKER_DEBUG_IMAGES environment variable is not set.

    Args:
        image: PIL Image object to save.
        name: Descriptive name for the image (e.g., "after_grayscale").
              Avoid special characters; use underscores instead.

    Example:
        from factchecker.debug_utils import dump_image_debug
        dump_image_debug(processed_image, "before_ocr")
    """
    if not os.getenv("FACTCHECKER_DEBUG_IMAGES"):
        return

    DEBUG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S_%f")[:-3]
    filename = DEBUG_DIR / f"{timestamp}_{name}.png"
    image.save(filename)
    print(f"[DEBUG] Image saved: {filename}")
