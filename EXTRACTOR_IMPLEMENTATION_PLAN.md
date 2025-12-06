# Technical Approach for Extractor Implementation

## Current State Analysis

The FactChecker project has skeleton implementations of `TextExtractor` and `ImageExtractor` that:
- Both extend `BaseExtractor` interface
- Currently return basic `ExtractedClaim` objects with minimal processing
- Have placeholder logic marked with TODOs
- Are tested with basic unit tests (5 tests for TextExtractor, 4 for ImageExtractor)
- The pipeline calls `self.extractors.extract()` but routing logic is not yet implemented

## Architecture Decisions

### 1. Parallel Extractor Execution
**Decision**: Run both `TextExtractor` and `ImageExtractor` in parallel when inputs are available, rather than routing to a single extractor.

**Rationale**: 
- Allows both extractors to process their respective inputs concurrently
- Enables ClaimCombiner to merge results from both sources
- Better separation of concerns - each extractor handles its domain
- Supports hybrid inputs more effectively

**Implementation**:
- Modify pipeline `_extract_claim()` to run extractors in parallel using `asyncio.gather()`
- TextExtractor processes `claim_text` if available
- ImageExtractor processes `image_data` if available
- Both return `ExtractedClaim` objects (or None if input not available)
- Results passed to ClaimCombiner stage

### 2. ClaimCombiner Stage
**Decision**: Create a new `ClaimCombiner` class that merges extractor outputs and generates granular questions.

**Rationale**:
- Separates extraction logic from claim synthesis
- Enables question generation for structured search
- Handles merging of text from multiple sources (text + OCR)
- Generates searchable questions (who, when, where, what) for next pipeline stage

**Implementation**:
- Create `src/factchecker/extractors/claim_combiner.py`
- Input: Optional `ExtractedClaim` from TextExtractor, Optional `ExtractedClaim` from ImageExtractor
- Output: Single enhanced `ExtractedClaim` with:
  - Combined `claim_text` (merged from both sources)
  - `questions` field: List of structured questions
  - Enhanced metadata
  - Combined confidence score

**Question Generation Strategy**:
- **MVP Approach**: Rule-based question generation using pattern matching
  - Extract entities (names, dates, locations) using regex patterns
  - Generate questions based on detected entities:
    - "Who" questions for person names
    - "When" questions for dates/times
    - "Where" questions for locations
    - "What" questions for main claim content
- **Future (v0.1+)**: NLP-based using spaCy for entity recognition and question generation

**Question Structure**:
- Add `questions` field to `ExtractedClaim` model: `List[ClaimQuestion]`
- Create `ClaimQuestion` model with:
  - `question_type`: Literal["who", "when", "where", "what", "how", "why"]
  - `question_text`: str
  - `related_entity`: Optional[str] (the entity this question targets)
  - `confidence`: float (confidence in question relevance)

### 3. TextExtractor Implementation Strategy

**Core Functionality**:
1. **Text Normalization**:
   - Strip whitespace, normalize unicode
   - Handle encoding issues gracefully
   - Remove excessive whitespace/newlines
   - Preserve original for metadata

2. **Claim Extraction** (MVP - simple approach):
   - For MVP: return normalized text as-is (current behavior)
   - Add basic validation (min/max length)
   - Extract basic metadata (word count, sentence count, language detection if feasible)
   - **Future (v0.1+)**: NLP-based claim segmentation using spaCy

3. **Confidence Scoring**:
   - Base confidence on text quality metrics:
     - Length appropriateness (not too short/long)
     - Character encoding validity
     - Presence of meaningful content

4. **Metadata Collection**:
   - `text_length`: Character count
   - `word_count`: Word count
   - `sentence_count`: Approximate sentence count
   - `encoding`: Detected encoding
   - `normalized`: Whether normalization was applied
   - `has_image`: Boolean flag

**Dependencies**: 
- No new dependencies for MVP (use stdlib `re`, `unicodedata`)
- Future: `spacy` or `nltk` for advanced NLP (Phase 2.4)

### 4. ImageExtractor Implementation Strategy

**Core Functionality**:
1. **Image Validation**:
   - Validate image format (JPEG, PNG, GIF, WebP)
   - Check image size limits (max dimensions, file size)
   - Verify image is readable/not corrupted
   - Use `PIL/Pillow` for format detection

2. **Image Preprocessing** (for OCR quality):
   - Convert to RGB if needed
   - Optional: grayscale conversion for better OCR
   - Optional: contrast enhancement (future enhancement)
   - Resize if too large (to prevent OCR timeout)

3. **OCR Processing**:
   - Use `pytesseract` (already in requirements.txt)
   - Extract text with confidence scores
   - Handle OCR errors gracefully
   - Support multiple languages (configurable)

4. **Text Extraction**:
   - Extract OCR text from image
   - Return as `ExtractedClaim` with OCR metadata
   - Note: Text combination happens in ClaimCombiner, not here

5. **Confidence Scoring**:
   - Base on OCR confidence score
   - Penalize if OCR fails or returns low confidence
   - Consider image quality factors

6. **Metadata Collection**:
   - `image_size`: Bytes
   - `image_format`: Detected format (JPEG, PNG, etc.)
   - `image_dimensions`: Width x height
   - `ocr_confidence`: OCR confidence score (0-100)
   - `ocr_text_length`: Length of extracted OCR text
   - `ocr_language`: Language used for OCR
   - `preprocessing_applied`: List of preprocessing steps

**Dependencies**:
- `pytesseract>=0.3.10` (already in requirements.txt)
- `pillow>=10.0.0` (already in requirements.txt)
- System dependency: Tesseract OCR binary (document in setup)

### 5. Error Handling Strategy

**Common Error Scenarios**:
1. **TextExtractor**:
   - Empty text after normalization → Lower confidence, return empty string
   - Encoding errors → Log warning, attempt recovery, return with low confidence
   - Extremely long text → Truncate with warning, include in metadata

2. **ImageExtractor**:
   - Unsupported image format → Raise `ValueError` with clear message
   - Corrupted image → Raise `ValueError` with details
   - OCR failure → Log error, return with low confidence, include error in metadata
   - Tesseract not installed → Raise `RuntimeError` with installation instructions

3. **ClaimCombiner**:
   - Both extractors return None → Return error claim with low confidence
   - Text merging conflicts → Prefer higher confidence source, log warning
   - Question generation fails → Return claim without questions, log warning

**Error Response Pattern**:
- Never raise exceptions that crash pipeline (pipeline handles errors)
- Return `ExtractedClaim` with low confidence and error details in metadata
- Log errors with appropriate level (WARNING for recoverable, ERROR for failures)

### 6. Logging Integration

**Logging Points**:
- Extract start/completion with input type
- OCR processing start/completion with confidence
- Text normalization steps (if verbose)
- Claim combination and question generation
- Error conditions with context
- Performance metrics (extraction time)

**Use existing logging infrastructure**:
- `get_logger(__name__)` for module logger
- `@log_stage` decorator not needed (extractors are called within pipeline stage)
- Include request ID from context (already propagated)

### 7. Testing Strategy

**TextExtractor Tests** (extend existing):
- Edge cases: empty strings, very long text, special characters
- Encoding tests: UTF-8, Latin-1, emoji handling
- Normalization verification
- Confidence scoring validation
- Metadata accuracy

**ImageExtractor Tests** (extend existing):
- Image format handling (JPEG, PNG, GIF)
- OCR with sample images (use test fixtures)
- OCR failure handling
- Binary data validation
- Image preprocessing verification

**ClaimCombiner Tests** (new):
- Text-only combination
- Image-only combination
- Hybrid combination (text + image)
- Question generation for various claim types
- Confidence score merging
- Edge cases (empty inputs, conflicting data)

**Integration Tests**:
- Parallel extractor execution
- Pipeline integration with real extractors
- Error propagation through pipeline
- Question usage in search parameter building

## Implementation Order

1. **Phase 1: Model Updates** (foundation)
   - Add `ClaimQuestion` model to `core/models.py`
   - Add `questions` field to `ExtractedClaim` model
   - Update model validation and tests

2. **Phase 2: TextExtractor Enhancement**
   - Implement text normalization
   - Add validation and edge case handling
   - Enhance metadata collection
   - Extend test suite

3. **Phase 3: ImageExtractor OCR Integration**
   - Integrate pytesseract
   - Implement image validation
   - Add preprocessing pipeline
   - Implement error handling
   - Extend test suite

4. **Phase 4: ClaimCombiner Implementation**
   - Create ClaimCombiner class
   - Implement text merging logic
   - Implement rule-based question generation
   - Add confidence score merging
   - Create test suite

5. **Phase 5: Pipeline Integration**
   - Update pipeline to run extractors in parallel
   - Integrate ClaimCombiner stage
   - Update search parameter building to use questions
   - End-to-end testing
   - Performance optimization
   - Documentation

## Files to Modify/Create

**New Files**:
- `src/factchecker/extractors/claim_combiner.py` - ClaimCombiner implementation
- `src/factchecker/extractors/tests/test_claim_combiner.py` - ClaimCombiner tests

**Modify Existing Files**:
- `src/factchecker/core/models.py` - Add ClaimQuestion model, update ExtractedClaim
- `src/factchecker/extractors/text_extractor.py` - Add real text processing
- `src/factchecker/extractors/image_extractor.py` - Add OCR implementation
- `src/factchecker/extractors/__init__.py` - Export ClaimCombiner
- `src/factchecker/extractors/tests/test_text_extractor.py` - Add edge case tests
- `src/factchecker/extractors/tests/test_image_extractor.py` - Add OCR tests
- `src/factchecker/pipeline/factcheck_pipeline.py` - Update extraction stage for parallel execution
- `src/factchecker/pipeline/factcheck_pipeline.py` - Add ClaimCombiner stage
- `src/factchecker/core/tests/test_models.py` - Test new model fields (if exists)

**Configuration**:
- Update `.env.example` if OCR language/config needed
- Document Tesseract installation in README

## Dependencies

**Already Available**:
- `pytesseract>=0.3.10`
- `pillow>=10.0.0`
- Standard library: `re`, `unicodedata`, `io`, `asyncio`

**Future (v0.1+)**:
- `spacy` or `nltk` for advanced NLP (Phase 2.4)

## Data Model Changes

### New Model: ClaimQuestion
```python
class ClaimQuestion(BaseModel):
    """A granular question about a claim aspect."""
    question_type: Literal["who", "when", "where", "what", "how", "why"]
    question_text: str
    related_entity: Optional[str] = None
    confidence: float  # 0.0 to 1.0
```

### Updated Model: ExtractedClaim
Add field:
```python
questions: List[ClaimQuestion] = []
```

## Pipeline Flow Changes

**Current Flow**:
1. Cache Lookup
2. Extract Claim (single extractor)
3. Build Search Parameters
4. Search Sources
5. Generate Response
6. Cache Response

**New Flow**:
1. Cache Lookup
2. Extract Claims (parallel: TextExtractor + ImageExtractor)
3. **Combine Claims** (new ClaimCombiner stage)
4. Build Search Parameters (uses questions from combined claim)
5. Search Sources
6. Generate Response
7. Cache Response

## Success Criteria

1. TextExtractor handles all text input types with proper normalization
2. ImageExtractor successfully extracts text from images using OCR
3. ClaimCombiner merges extractor outputs correctly
4. ClaimCombiner generates relevant questions (who, when, where, what)
5. Questions are used effectively in search parameter building
6. All edge cases handled gracefully without pipeline crashes
7. Comprehensive test coverage (target: 95% for extractors)
8. Integration with pipeline works end-to-end
9. Error handling preserves request ID and logs appropriately
10. Parallel execution improves performance for hybrid inputs

## Open Questions / Future Considerations

1. **Question Quality**: How to validate question quality? Should we filter low-confidence questions?
2. **Question Limits**: Should there be a maximum number of questions per claim?
3. **Question Prioritization**: Should questions be ranked/prioritized for search?
4. **NLP Integration**: When to upgrade from rule-based to NLP-based question generation?
5. **Multi-language Support**: How to handle question generation for non-English claims?
6. **Question Caching**: Should generated questions be cached with the claim?


