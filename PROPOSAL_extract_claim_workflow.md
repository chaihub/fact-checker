# Proposal: Rewrite `_extract_claim()` Stage Based on Page-3 Workflow

## Overview
This proposal outlines a fresh implementation of the `_extract_claim()` stage that follows the workflow defined in Page-3 of `factchecker.drawio`.

## Workflow Summary (from Page-3)

The workflow handles multiple input scenarios:
1. **Text input** → Extract claim from text
2. **Image input (text image)** → Extract text from image, with potential nested image handling
3. **Combined inputs** → Multiple extraction paths that can be combined

### Decision Flow:
1. Start: Receive claim input (text and/or image)
2. Check: "Text in input?"
   - Yes → Extract claim from text → Output A
   - No → Continue to image processing
3. Check: "Text image in input?"
   - Yes → Continue to image processing
   - No → Return existing outputs
4. Check: "Text image inside text image?" (nested images)
   - Yes → Separate inside text image, extract top text, extract inside text
   - No → Extract text from text image directly

### Output Scenarios:
- **Output A**: Text claim (from text input)
- **Output B**: Image text claim (from single image)
- **Outputs C, D**: Top image claim and inside image claim (from nested images)
Note: When multiple claims are extracted, they are NOT combined. The function returns the text claim if available, otherwise returns the first image claim.

## Proposed Implementation Structure

### New Function Signatures (to be added to extractors)

```python
# In extractors/image_handler.py (new file)
class ImageHandler:
    """Handles image processing including nested image detection and separation."""
    
    async def detect_text_image(self, image_data: bytes) -> bool:
        """Check if image contains readable text (is a 'text image')."""
        pass
    
    async def detect_nested_image(self, image_data: bytes) -> bool:
        """Check if text image contains another image inside it."""
        pass
    
    async def separate_nested_image(self, image_data: bytes) -> tuple[bytes, bytes]:
        """Separate top image and inside image. Returns (top_image, inside_image)."""
        pass
    
    async def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from a single image using OCR."""
        pass

# In extractors/text_image_extractor.py (new file, or extend ImageExtractor)
class TextImageExtractor:
    """Extracts claims from text images (images containing text)."""
    
    async def extract_from_text_image(
        self, image_data: bytes
    ) -> ExtractedClaim:
        """Extract claim from a text image."""
        pass
    
    async def extract_from_top_image(
        self, top_image_data: bytes
    ) -> ExtractedClaim:
        """Extract claim from top text image."""
        pass
    
    async def extract_from_inside_image(
        self, inside_image_data: bytes
    ) -> ExtractedClaim:
        """Extract claim from inside text image."""
        pass

```

### New `_extract_claim()` Implementation

```python
@log_stage("Claim Extraction")
async def _extract_claim(self, request: FactCheckRequest) -> ExtractedClaim:
    """Extract structured claim from text and/or image following Page-3 workflow.
    
    Workflow:
    1. If text exists → Extract text claim (Output A)
    2. If image exists → Check if text image
    3. If text image → Check if nested
    4. Extract from appropriate sources
    5. Return text claim if available, otherwise return first image claim
    """
    text_claim: Optional[ExtractedClaim] = None
    image_claims: List[ExtractedClaim] = []
    
    # Step 1: Extract text claim if text input exists
    if request.claim_text:
        text_claim = await self._extract_text_claim(request.claim_text)  # Output A
    
    # Step 2: Process image if present
    if request.image_data:
        image_claims = await self._process_image_input(request.image_data)
    
    # Step 3: Return text claim if available, otherwise return first image claim
    if text_claim:
        return text_claim
    elif image_claims:
        return image_claims[0]
    else:
        # Error case: no claims extracted
        return self._create_error_claim("No claims extracted from input")

async def _extract_text_claim(self, claim_text: str) -> Optional[ExtractedClaim]:
    """Extract claim from text input. Returns Output A."""
    return await self.text_extractor.extract(claim_text, None)

async def _process_image_input(
    self, image_data: bytes
) -> List[ExtractedClaim]:
    """Process image input following workflow decisions.
    
    Returns list of ExtractedClaim objects from image processing.
    """
    claims: List[ExtractedClaim] = []
    
    # Check if this is a text image
    is_text_image = await self.image_handler.detect_text_image(image_data)
    
    if not is_text_image:
        # Not a text image - basic image extraction
        image_claim = await self.text_image_extractor.extract_from_text_image(image_data)
        if image_claim:
            claims.append(image_claim)  # Output B
        return claims
    
    # It's a text image - check for nesting
    has_nested_image = await self.image_handler.detect_nested_image(image_data)
    
    if has_nested_image:
        # Nested image case: separate and extract from both
        top_image, inside_image = await self.image_handler.separate_nested_image(image_data)
        
        # Extract from top image
        top_claim = await self.text_image_extractor.extract_from_top_image(top_image)
        if top_claim:
            claims.append(top_claim)  # Output C
        
        # Extract from inside image
        inside_claim = await self.text_image_extractor.extract_from_inside_image(inside_image)
        if inside_claim:
            claims.append(inside_claim)  # Output D
    else:
        # Simple text image: extract directly
        image_claim = await self.text_image_extractor.extract_from_text_image(image_data)
        if image_claim:
            claims.append(image_claim)  # Output B
    
    return claims

def _create_error_claim(self, error_message: str) -> ExtractedClaim:
    """Create an error ExtractedClaim when extraction fails."""
    return ExtractedClaim(
        claim_text="",
        extracted_from="hybrid",
        confidence=0.0,
        raw_input_type="both",
        metadata={"error": error_message},
        questions=[],
    )
```

### Required Changes to Pipeline Class

```python
class FactCheckPipeline(IPipeline):
    def __init__(self, cache, extractors, searchers, processors):
        self.cache = cache
        self.searchers = searchers
        self.processors = processors
        
        # Existing extractors
        self.text_extractor: TextExtractor = extractors.get("text")
        self.image_extractor: ImageExtractor = extractors.get("image")
        
        # New components for Page-3 workflow
        self.image_handler: ImageHandler = extractors.get("image_handler", ImageHandler())
        self.text_image_extractor: TextImageExtractor = extractors.get(
            "text_image_extractor", TextImageExtractor()
        )
```

## Data Structures

All functions will continue to use the existing `ExtractedClaim` model:
- `claim_text`: str (the extracted/combined text)
- `extracted_from`: Literal["image", "text", "hybrid"]
- `confidence`: float
- `raw_input_type`: Literal["text_only", "image_only", "both"]
- `metadata`: dict
- `questions`: List[ClaimQuestion]

## Implementation Notes

1. **High-level flow first**: This proposal focuses on structure and function signatures
2. **Detailed implementation later**: Image detection, separation, and extraction logic will be implemented in subsequent tasks
3. **Backward compatibility**: Existing extractors remain available but workflow changes
4. **Error handling**: Each step should handle failures gracefully
5. **Async/await**: All extraction steps remain async for concurrent processing where possible

## Next Steps

1. Create `ImageHandler` class with placeholder methods
2. Create/extend `TextImageExtractor` class  
3. Replace `_extract_claim()` implementation
4. Update pipeline initialization to include new components
5. Add error handling and logging
6. Implement detailed logic for each step (detection, separation, extraction)



