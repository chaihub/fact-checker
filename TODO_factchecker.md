# FactChecker Implementation Tasks

---

## 🚀 START HERE

### Current Priority Tasks
- Implement claim verification for one external source within each source category
- Add a feature to specify if the match is exact or approximate
---

## Overview
This document tracks all granular tasks for implementing the FactChecker component. Tasks are organized by phase and priority. Each task includes implementation and testing requirements.

---

## Phase 0: Setup & Project Configuration

### 0.1 Project Dependencies
- [x] **0.1.1** Create `requirements.txt` with core dependencies
  - pydantic >= 2.0
  - pytest >= 7.0
  - pytest-asyncio >= 0.21
  - aiohttp >= 3.8
  - pytesseract (for OCR)
  - fastapi, uvicorn, tweepy, sqlalchemy, pillow, and others
- [x] **0.1.2** Create `requirements-dev.txt` with dev dependencies
  - ruff, mypy, black, pytest-cov, pytest-mock
  - Additional: pytest-xdist, sphinx, ipdb, responses, freezegun

### 0.2 Configuration Files
- [x] **0.2.1** Create `pytest.ini` with test configuration
  - Test discovery patterns, asyncio mode, markers, logging, coverage
- [x] **0.2.2** Create `mypy.ini` for strict type checking
  - Python 3.10+, strict mode, per-module overrides
- [x] **0.2.3** Create `.env.example` for environment variables
  - Twitter, BlueSky, WhatsApp, database, cache, API config
- [x] **0.2.4** Create `pyproject.toml` with project metadata
  - Build system, project metadata, tool configs (ruff, mypy, black, coverage)

### 0.3 CI/CD & Testing Infrastructure
- [ ] **0.3.1** Create GitHub Actions workflow for tests
- [ ] **0.3.2** Setup code coverage reporting
- [ ] **0.3.3** Setup pre-commit hooks for linting

### 0.4 LLM Configuration System Setup
- [x] **0.4.1** Add LLM provider dependencies to `requirements.txt`
  - Add `google-generativeai` (for Google Gemini) ✅
  - Add `httpx` (already present for async HTTP) ✅
- [x] **0.4.2** Create `.env` variables for LLM API keys
  - `GOOGLE_GEMINI_API_KEY` - API key for Google Gemini ✅
  - `DEFAULT_LLM_PROVIDER` - Provider selection (default: "google-gemini") ✅
  - `LLM_API_TIMEOUT` - API timeout in seconds ✅
  - `LLM_MAX_TOKENS` - Maximum tokens per request ✅
  - `LLM_TEMPERATURE` - Model temperature setting ✅
- [x] **0.4.3** Add LLM configuration to `pyproject.toml` if needed
  - Tool-specific LLM settings (e.g., default timeouts) ✅
  - Use case configurations for claim extraction ✅ (#CR#: But not sure if this was really necessary)

---

## Phase 1: Core Models & Logging

### 1.1 Models Implementation
- [x] **1.1.1** Implement `FactCheckRequest` model with validation
- [x] **1.1.2** Implement `ExtractedClaim` model
- [x] **1.1.3** Implement `SearchResult` model
- [x] **1.1.4** Implement `VerdictEnum` enum
- [x] **1.1.5** Implement `Evidence` model
- [x] **1.1.6** Implement `Reference` model
- [x] **1.1.7** Implement `FactCheckResponse` model
- [x] **1.1.9** Add `ClaimQuestion` model for granular questions
  - `question_type`: Literal["who", "when", "where", "what", "how", "why"]
  - `question_text`: str
  - `related_entity`: Optional[str]
  - `confidence`: float
- [x] **1.1.10** Update `ExtractedClaim` model with `questions` field
  - Add `questions: List[ClaimQuestion] = []` field
  - Update model validation
- [x] **1.1.8** Add model validation tests
  - Test all required fields
  - Test optional fields
  - Test enum constraints
  - Test nested model validation
  - [x] Test ClaimQuestion model validation
  - [x] Test ExtractedClaim with questions field

### 1.2 Logging Implementation
- [x] **1.2.1** Implement `setup_logging()` function
- [x] **1.2.2** Implement `get_logger()` with context injection
- [x] **1.2.3** Implement `request_id_var` context variable
- [x] **1.2.4** Implement `@log_stage` decorator
- [x] **1.2.5** Write logging configuration tests ✅ COMPLETE (31/31 tests passing)
  - [x] Test context variable injection (5 tests)
  - [x] Test decorator timing (6 tests)
  - [x] Test log formatting (6 tests)
  - [x] Test error logging (6 tests)
  - [x] Test logging integration (4 tests)
  - [x] Test edge cases (4 tests)

### 1.3 Interfaces Implementation
- [x] **1.3.1** Implement `BaseExtractor` abstract class
- [x] **1.3.2** Implement `BaseSearcher` abstract class
- [x] **1.3.3** Implement `BaseProcessor` abstract class
- [x] **1.3.4** Implement `IPipeline` interface
- [x] **1.3.5** Write interface tests ✅ COMPLETE (60/60 tests passing)
  - [x] Verify abstract classes cannot be instantiated (5 tests)
  - [x] Verify abstract methods exist and are marked (8 tests)
  - [x] Test TextExtractor compliance with BaseExtractor (4 tests)
  - [x] Test ImageExtractor compliance with BaseExtractor (4 tests)
  - [x] Test TwitterSearcher compliance with BaseSearcher (5 tests)
  - [x] Test BlueSkySearcher compliance with BaseSearcher (5 tests)
  - [x] Test ResultAnalyzer implementation (3 tests)
  - [x] Test ResponseGenerator implementation (3 tests)
  - [x] Test method signature contracts (8 tests)
  - [x] Test dependency injection patterns (5 tests)
  - [x] Test method implementations and overrides (6 tests)
  - [x] Test property behavior and enforcement (4 tests)

---

## Phase 2: Extractors Module

### 2.1 TextExtractor Implementation
- [x] **2.1.1** Create `TextExtractor` class extending `BaseExtractor`
- [x] **2.1.2** Implement `extract()` method for text input
- [x] **2.1.3** Implement input type detection logic
- [x] **2.1.4** Implement metadata collection
- [x] **2.1.6** Implement text normalization
  - Strip whitespace, normalize unicode
  - Handle encoding issues gracefully
  - Remove excessive whitespace/newlines
  - Preserve original for metadata
- [x] **2.1.7** Add text validation and edge case handling
  - Validate min/max length
  - Handle empty text after normalization (raises ValueError)
  - Handle encoding errors (log warning, attempt recovery)
  - Handle extremely long text (truncate with warning)
- [x] **2.1.8** Enhance metadata collection
  - Add `word_count`: Word count
  - Add `sentence_count`: Approximate sentence count
  - Add `encoding`: Detected encoding
  - Add `normalized`: Whether normalization was applied
  - Keep existing: `text_length`, `has_image`
- [x] **2.1.5** Unit test TextExtractor
  - [x] Test basic text extraction
  - [x] Test input validation (no claim_text + no image_data fails)
  - [x] Test hybrid extraction (both inputs)
  - [x] Test image-only extraction
  - [x] Test metadata population
  - [x] Test edge cases (empty strings, very long text)
  - [x] Test special characters and encoding
  - [x] Test text normalization
  - [x] Test encoding error handling

### 2.2 ImageExtractor Implementation
- [x] **2.2.1** Create `ImageExtractor` class extending `BaseExtractor`
- [x] **2.2.2** Implement `extract()` method for image input
- [x] **2.2.3** Implement input type detection logic
- [x] **2.2.4** Add placeholder for OCR logic
- [x] **2.2.6** Implement image validation ✅ COMPLETE
  - [x] Validate image format (JPEG, PNG, GIF, WebP)
  - [x] Check image size limits (max dimensions, file size)
  - [x] Verify image is readable/not corrupted
  - [x] Use PIL/Pillow for format detection
  - [x] Handle unsupported formats (raise ValueError with clear message)
  - [x] Handle corrupted images (raise ValueError with details)
- [x] **2.2.7** Implement image preprocessing pipeline ✅ COMPLETE
  - [x] Convert to RGB if needed
  - [x] Grayscale conversion for better OCR
  - [x] Resize if too large (to prevent OCR timeout)
  - [x] Track preprocessing steps in metadata
- [x] **2.2.8** Integrate pytesseract OCR processing ✅ COMPLETE
  - [x] Extract text with confidence scores
  - [x] Handle OCR errors gracefully
  - [x] Support multiple languages (configurable)
  - [x] Handle Tesseract not installed gracefully
  - [x] Return OCR text as ExtractedClaim with OCR metadata
- [x] **2.2.9** Implement OCR confidence scoring ✅ COMPLETE
  - [x] Base on OCR confidence score (0-100)
  - [x] Penalize if OCR fails or returns low confidence
  - [x] Consider image quality factors
- [x] **2.2.10** Enhance metadata collection ✅ COMPLETE
  - [x] Add `image_format`: Detected format (JPEG, PNG, etc.)
  - [x] Add `image_dimensions`: Width x height
  - [x] Add `ocr_confidence`: OCR confidence score (0-100)
  - [x] Add `ocr_text_length`: Length of extracted OCR text
  - [x] Add `ocr_language`: Language used for OCR
  - [x] Add `preprocessing_applied`: List of preprocessing steps
  - [x] Keep existing: `image_size`
- [x] **2.2.5** Unit test ImageExtractor ✅ COMPLETE (32/32 tests)
   - [x] Test basic image extraction
   - [x] Test input validation
   - [x] Test hybrid extraction
   - [x] Test metadata capture
   - [x] Test image format handling (JPEG, PNG, GIF, WebP)
   - [x] Test binary data validation
   - [x] Test image validation (corrupted, unsupported formats)
   - [x] Test OCR with sample images (use test fixtures)
   - [x] Test OCR failure handling
   - [x] Test image preprocessing verification
   - [x] Test OCR confidence scoring

### 2.3 LLM-Based Claim Extraction
- [x] **2.3.1** Implement LLM-based text claim extraction using AI API
  - Use `claim_extraction_from_text` use case from LLM config
  - Call Google Gemini API with extracted text
  - Parse and structure LLM response into ExtractedClaim
  - Extract claim segments and key assertions
  - Assign confidence scores based on LLM confidence
  - Handle LLM API errors gracefully (fallback to text-only extraction)
- [ ] **2.3.2** Implement LLM-based image claim extraction using multiple questions
  - Use `claim_extraction_from_image` use case from LLM config
  - Send OCR'd image text + image metadata to LLM
  - Generate multiple clarifying questions (who, what, when, where, why)
  - Extract structured claims from LLM responses
  - Combine question answers into unified claim
  - Handle multi-turn LLM conversation if needed
- [ ] **2.3.3** Test LLM-based extraction
  - Mock LLM API responses in tests
  - Test with various claim types and formats
  - Test error handling for LLM API failures
  - Test confidence score generation
- [ ] **2.3.4** Implement LLM response parsing and validation
  - Validate LLM output structure
  - Extract claims, questions, and confidence scores
  - Handle malformed responses gracefully

---

## Phase 3: Searchers Module

### 3.1 TwitterSearcher Implementation
- [x] **3.1.1** Create `TwitterSearcher` class extending `BaseSearcher`
- [x] **3.1.2** Add Twitter API client initialization
- [x] **3.1.3** Add `platform_name` property
- [ ] **3.1.4** Implement `search()` method
  - [ ] Build search query from claim
  - [ ] Handle query parameter passing
  - [ ] Call Twitter API
  - [ ] Parse and format results
  - [ ] Handle pagination
  - [ ] Handle rate limiting
- [ ] **3.1.5** Unit test TwitterSearcher
  - [x] Test initialization
  - [x] Test platform_name property
  - [x] Test search returns list
  - [x] Test search with parameters
  - [ ] Test API error handling
  - [ ] Test result parsing
  - [ ] Test pagination logic
  - [ ] Test rate limit handling
- [ ] **3.1.6** Add Twitter API configuration
  - [ ] Add `.env` variables for API keys
  - [ ] Add environment validation

### 3.2 BlueSkySearcher Implementation (v0.1)
- [x] **3.2.1** Create `BlueSkySearcher` class extending `BaseSearcher`
- [x] **3.2.2** Add BlueSky API client placeholder
- [x] **3.2.3** Add `platform_name` property
- [ ] **3.2.4** Implement `search()` method
  - [ ] Implement BlueSky authentication
  - [ ] Build search query
  - [ ] Call BlueSky API
  - [ ] Parse and format results
  - [ ] Handle BlueSky-specific fields
- [ ] **3.2.5** Unit test BlueSkySearcher
  - [x] Test initialization
  - [x] Test platform_name property
  - [x] Test search returns list
  - [ ] Test authentication
  - [ ] Test API error handling
- [ ] **3.2.6** Add BlueSky API configuration

### 3.3 LLM-Based Search Query Generation
- [ ] **3.3.1** Create `SearchQueryBuilder` class using LLM
  - Use `search_query_generation` use case from LLM config
  - Accept claim text or extracted claim with questions
  - Call LLM to generate optimized search queries
  - Generate multiple query variations for redundancy
  - Return list of SearchQuery objects with priority/confidence
- [ ] **3.3.2** Implement fallback query generation (non-LLM)
  - Extract key terms/entities from claim if LLM unavailable
  - Create simple keyword-based search queries
  - Use for robustness when LLM fails
- [ ] **3.3.3** Test LLM-based query generation
  - Mock LLM API responses
  - Test with various claim types
  - Test fallback behavior
  - Compare LLM-generated vs. fallback queries

### 3.4 Search Result Aggregation
- [ ] **3.4.1** Create `SearchAggregator` class
- [ ] **3.4.2** Implement concurrent searcher execution
- [ ] **3.4.3** Implement error handling & graceful degradation
- [ ] **3.4.4** Implement deduplication logic
- [ ] **3.4.5** Test result aggregation
  - [ ] Test concurrent execution
  - [ ] Test error handling
  - [ ] Test deduplication

---

## Phase 4: Processors Module

### 4.1 ResultAnalyzer Implementation
- [x] **4.1.1** Create `ResultAnalyzer` class extending `BaseProcessor`
- [x] **4.1.2** Add placeholder for analysis logic
- [ ] **4.1.3** Implement verdict determination logic
  - [ ] Implement claim-vs-result comparison
  - [ ] Implement confidence scoring
  - [ ] Implement evidence extraction
  - [ ] Handle edge cases (no results, conflicting results)
- [ ] **4.1.4** Unit test ResultAnalyzer
  - [x] Test analysis with results
  - [x] Test analysis without results
  - [ ] Test verdict generation
  - [ ] Test confidence calculation
  - [ ] Test various claim types
- [ ] **4.1.5** Implement advanced NLP comparison
  - [ ] Add semantic similarity scoring
  - [ ] Add negation handling
  - [ ] Add temporal logic

### 4.2 LLM-Based Response Generation
- [x] **4.2.1** Create `ResponseGenerator` class extending `BaseProcessor`
- [x] **4.2.2** Add placeholder for response generation
- [ ] **4.2.3** Implement LLM-based response formatting
  - Use `response_generation` use case from LLM config
  - Send claim + search results to LLM
  - LLM generates human-readable verdict and explanation
  - Extract confidence score from LLM response
  - Generate evidence summary and references
- [ ] **4.2.4** Implement fallback response generation (non-LLM)
  - Rule-based verdict determination if LLM unavailable
  - Simple template-based explanation
  - Reference extraction from search results
- [ ] **4.2.5** Unit test ResponseGenerator
  - [x] Test response generation
  - [x] Test response structure
  - [ ] Test LLM explanation generation
  - [ ] Test evidence formatting
  - [ ] Test reference extraction
  - [ ] Test fallback behavior
- [ ] **4.2.6** Implement WhatsApp-specific formatting
  - [ ] Format for character limits
  - [ ] Handle markdown to WhatsApp format

### 4.3 Claim-Specific Processors (v0.1+)
- [ ] **4.3.1** Create specialized processors for different claim types
  - [ ] QuoteVerificationProcessor
  - [ ] ImageVerificationProcessor
  - [ ] DateClaimProcessor
  - [ ] NamedEntityProcessor
- [ ] **4.3.2** Implement claim type detection
- [ ] **4.3.3** Route to appropriate processor
- [ ] **4.3.4** Test specialized processors

---

## Phase 5: Storage Module

### 5.1 Cache Implementation
- [x] **5.1.1** Create `Cache` class with in-memory storage
- [x] **5.1.2** Implement `get()` method with TTL checking
- [x] **5.1.3** Implement `set()` method with TTL
- [x] **5.1.4** Implement `clear()` and `size()` methods
- [ ] **5.1.5** Unit test Cache
  - [x] Test set and get
  - [x] Test cache miss
  - [x] Test cache clear
  - [x] Test TTL expiration
  - [ ] Test concurrent access
  - [ ] Test large payload handling
  - [ ] Test memory limits

### 5.2 Database Implementation
- [x] **5.2.1** Create `Database` class with SQLite interface
- [x] **5.2.2** Add database initialization
- [ ] **5.2.3** Implement schema creation
  - [ ] Create `claims` table
  - [ ] Create `fact_checks` table
  - [ ] Create `search_results` table
  - [ ] Add appropriate indexes
- [ ] **5.2.4** Implement `save_response()` method
- [ ] **5.2.5** Implement `get_response()` method
- [ ] **5.2.6** Implement `close()` method
- [ ] **5.2.7** Unit test Database
  - [ ] Test save and retrieve
  - [ ] Test schema creation
  - [ ] Test connection handling
  - [ ] Test query performance

### 5.3 Cache Strategy
- [ ] **5.3.1** Implement multi-level cache strategy
  - [ ] In-memory cache for hot queries
  - [ ] Database cache for persistent storage
  - [ ] TTL-based expiration
- [ ] **5.3.2** Implement cache invalidation logic
- [ ] **5.3.3** Test cache strategies
  - [ ] Test multi-level fallback
  - [ ] Test invalidation
  - [ ] Test consistency

### 5.4 Data Persistence (v0.1+)
- [ ] **5.4.1** Implement data export functionality
- [ ] **5.4.2** Implement data import functionality
- [ ] **5.4.3** Add data backup mechanisms
- [ ] **5.4.4** Test persistence

---

## Phase 6: Pipeline Orchestration

### 6.1 Pipeline Stages
- [x] **6.1.1** Create stage base class
- [x] **6.1.2** Create `CacheLookupStage`
- [x] **6.1.3** Create `ClaimExtractionStage`
- [x] **6.1.4** Create `SearchParameterBuildingStage`
- [x] **6.1.5** Create `ExternalSearchStage`
- [x] **6.1.6** Create `ResultProcessingStage`
- [x] **6.1.7** Create `ResponseGenerationStage`
- [x] **6.1.8** Create `CacheStorageStage`

### 6.2 Main Pipeline
- [x] **6.2.1** Create `FactCheckPipeline` class implementing `IPipeline`
- [x] **6.2.2** Implement `check_claim()` orchestration method
- [x] **6.2.3** Implement individual stage methods
  - [x] `_check_cache()` - Returns Optional[FactCheckResponse]
  - [x] `_extract_claim()` - Returns ExtractedClaim
  - [x] `_build_search_params()` - Returns dict with search parameters
  - [x] `_search_sources()` - Returns List[SearchResult] with 3 mock results
  - [x] `_generate_response()` - Returns properly typed FactCheckResponse
  - [x] `_cache_response()` - Stores response with type safety
- [x] **6.2.4a** Create mock implementations for all pipeline stages ✅ COMPLETE
  - [x] Mock `ClaimExtractionStage` via extractor call
  - [x] Mock `SearchParameterBuildingStage` with dummy search parameters
  - [x] Mock `ExternalSearchStage` with hardcoded search results (3 results)
  - [x] Mock response generation with template responses
  - [x] Cache lookup and storage with pass-through logic
  - [x] All methods have complete type hints
  - [x] Request ID propagation through all stages
  - [x] Comprehensive test suite (6 new tests)
- [x] **6.2.4b** End-to-end skeleton test ✅ COMPLETE
   - [x] Test full pipeline execution flow with all mocked stages
   - [x] Verify data flows correctly through all stages
   - [x] Test with sample `FactCheckRequest` inputs
   - [x] Verify output matches expected `FactCheckResponse` structure
   - [x] Test request ID propagation through all stages
- [x] **6.2.4c** Stage integration and composition test ✅ COMPLETE
   - [x] Test chaining of mocked stages together
   - [x] Test error propagation through pipeline
   - [x] Test logging/tracing at each stage
   - [x] Verify stage output becomes next stage input
- [x] **6.2.4d** Pipeline configuration validation ✅ COMPLETE
   - [x] Verify all required components are wired correctly
   - [x] Test dependency injection of mocks
   - [x] Validate configuration before execution
   - [x] Test component initialization order
- [x] **6.2.4** Implement request ID generation and tracing ✅ COMPLETE
   - [x] Generate unique request IDs for each claim check
   - [x] Trace request ID through all mocked stages
   - [x] Include request ID in all stage logging
- [x] **6.2.5** Implement basic error handling for skeleton ✅ COMPLETE
   - [x] Test exception propagation through mocked stages
   - [x] Test basic error recovery at stage level (skeleton scope only)
   - [x] Pipeline never raises exceptions—always returns FactCheckResponse with ERROR verdict
   - [x] Sensitive data automatically sanitized in error parameters
   - [x] Request ID preserved and propagated through error responses

### 6.3 Pipeline Integration
*Note: Move these higher priority after skeleton is working. These test real component integration with the mocked pipeline framework.*
- [x] **6.3.1** Update pipeline for parallel extractor execution ✅ COMPLETE
  - [x] Modified `_extract_claim()` to run TextExtractor and ImageExtractor in parallel using `asyncio.gather()`
  - [x] TextExtractor processes `claim_text` if available (returns ExtractedClaim or None)
  - [x] ImageExtractor processes `image_data` if available (returns ExtractedClaim or None)
  - [x] Handle extractor errors gracefully using `return_exceptions=True` in `asyncio.gather()`
  - [x] Extractors are called directly without helper functions
  - [x] Updated `__init__` to expect extractors dict with "text", "image", and optionally "combiner" keys
- [x] **6.3.2** Integrate ClaimCombiner into pipeline ✅ COMPLETE
  - [x] ClaimCombiner integrated directly within `_extract_claim()` method (not as separate stage)
  - [x] TextExtractor and ImageExtractor results passed to ClaimCombiner after parallel extraction
  - [x] Pipeline flow: Extract Claims (parallel) → Combine Claims (within same method) → Build Search Parameters
  - [x] ClaimCombiner initialized in `__init__` with default instance if not provided
- [ ] **6.3.3** Update search parameter building to use questions
  - Modify `_build_search_params()` to use questions from combined claim
  - Generate search queries from questions (who, when, where, what)
  - Fall back to claim text if no questions available
- [ ] **6.3.4** Wire searchers into pipeline
- [ ] **6.3.5** Wire processors into pipeline
- [ ] **6.3.6** Wire storage/cache into pipeline
- [ ] **6.3.7** Test integrated pipeline components
  - [ ] Test parallel extractor execution
  - [ ] Test real TextExtractor + ImageExtractor with pipeline
  - [ ] Test ClaimCombiner integration
  - [ ] Test question usage in search parameter building
  - [ ] Test real TwitterSearcher + BlueSkySearcher with pipeline
  - [ ] Test real ResultAnalyzer + ResponseGenerator with pipeline
  - [ ] Test Cache and Database integration
  - [ ] Verify component outputs match expected interface contracts
  - [ ] Test error propagation through pipeline with real components

---

## Phase 7: Unit Testing

### 7.1 Core Models Tests
- [ ] **7.1.1** Test `FactCheckRequest` validation
- [ ] **7.1.2** Test `ExtractedClaim` structure
- [ ] **7.1.3** Test `FactCheckResponse` structure
- [ ] **7.1.4** Test enum constraints
- [ ] **7.1.5** Test nested model validation

### 7.2 Logging Tests
- [ ] **7.2.1** Test context variable injection
- [ ] **7.2.2** Test `@log_stage` decorator
- [ ] **7.2.3** Test timing measurement
- [ ] **7.2.4** Test error logging

### 7.3 Extractor Module Tests
- [x] **7.3.1** TextExtractor unit tests (5 tests created)
  - [ ] Add edge case tests (empty strings, very long text)
  - [ ] Add encoding tests (UTF-8, Latin-1, emoji handling)
  - [ ] Add normalization verification tests
  - [ ] Add confidence scoring validation tests
  - [ ] Add performance tests
- [x] **7.3.2** ImageExtractor unit tests (4 tests created)
  - [ ] Add format handling tests (JPEG, PNG, GIF, WebP)
  - [ ] Add binary data validation tests
  - [ ] Add OCR tests with sample images
  - [ ] Add OCR failure handling tests
  - [ ] Add image preprocessing verification tests

### 7.3.1 LLM Configuration Module Tests
- [ ] **7.3.1.1** Test `llm_config.py`
  - [ ] Test `get_llm_config(use_case)` retrieval
  - [ ] Test all predefined use cases are accessible
  - [ ] Test validation of use case parameters
  - [ ] Test `list_available_use_cases()` returns complete list
- [ ] **7.3.1.2** Test `llm_provider.py`
  - [ ] Test GoogleGeminiProvider initialization
  - [ ] Test `call(use_case, prompt)` async method
  - [ ] Test error handling for API failures
  - [ ] Test configuration parameter passing
  - [ ] Test retry logic for transient failures
- [ ] **7.3.1.3** Test `llm_helpers.py`
  - [ ] Test `list_llm_options()` function
  - [ ] Test `validate_use_case()` validation
  - [ ] Test `query_provider_options()` API querying
  - [ ] Test option parsing and formatting

### 7.4 Searcher Module Tests
- [x] **7.4.1** TwitterSearcher unit tests (4 tests created)
  - [ ] Add API error handling tests
  - [ ] Add pagination tests
  - [ ] Add rate limiting tests
  - [ ] Add result parsing tests
- [x] **7.4.2** BlueSkySearcher unit tests (3 tests created)
  - [ ] Add authentication tests
  - [ ] Add API error tests

### 7.5 Processor Module Tests
- [x] **7.5.1** ResultAnalyzer unit tests (2 tests created)
  - [ ] Add verdict generation tests
  - [ ] Add confidence calculation tests
  - [ ] Add various claim type tests
- [x] **7.5.2** ResponseGenerator unit tests (1 test created)
  - [ ] Add explanation generation tests
  - [ ] Add evidence formatting tests
  - [ ] Add reference extraction tests

### 7.6 Storage Module Tests
- [x] **7.6.1** Cache unit tests (4 tests created)
  - [ ] Add concurrent access tests
  - [ ] Add memory limit tests
  - [ ] Add large payload tests
- [ ] **7.6.2** Database unit tests
  - [ ] Add schema tests
  - [ ] Add query tests
  - [ ] Add connection tests
  - [ ] Add transaction tests

---

## Phase 8: Component-Level Testing

### 8.1 Pipeline Tests
- [x] **8.1.1** Create test fixtures for common objects
- [x] **8.1.2** Test pipeline initialization
- [x] **8.1.3** Test pipeline cache hit behavior
- [ ] **8.1.4** Test full pipeline execution
- [ ] **8.1.5** Test error handling and recovery
- [ ] **8.1.6** Implement timeout handling
  - [ ] Test timeout at each pipeline stage
  - [ ] Test timeout recovery mechanisms
  - [ ] Test timeout configuration and validation
- [ ] **8.1.7** Implement partial failure graceful degradation
  - [ ] Test graceful handling of stage failures
  - [ ] Test fallback mechanisms
  - [ ] Test partial result return when stages fail
- [ ] **8.1.8** Test concurrent requests

### 8.2 Integrator Tests
- [ ] **8.2.1** Test extractor + searcher integration
- [ ] **8.2.2** Test searcher + processor integration
- [ ] **8.2.3** Test all components together
- [ ] **8.2.4** Test with mocked external APIs
- [ ] **8.2.5** Test cache behavior with real pipeline

---

## Phase 9: Integration Testing

### 9.1 End-to-End Tests
- [ ] **9.1.1** Create end-to-end test suite
- [ ] **9.1.2** Test full pipeline with all real components
- [ ] **9.1.3** Test with various claim types
- [ ] **9.1.4** Test error handling and recovery
- [ ] **9.1.5** Test cache behavior
- [ ] **9.1.6** Test concurrent requests
- [ ] **9.1.7** Test performance expectations
- [ ] **9.1.8** Test logging and tracing

### 9.2 WhatsApp Integration Tests
- [ ] **9.2.1** Create WhatsApp integration test suite
- [ ] **9.2.2** Test message routing to pipeline
- [ ] **9.2.3** Test response formatting
- [ ] **9.2.4** Test media/image handling
- [ ] **9.2.5** Test user session management
- [ ] **9.2.6** Test error response formatting
- [ ] **9.2.7** Test message chunking for long responses
- [ ] **9.2.8** Test concurrent user requests

### 9.3 Twitter API Integration Tests
- [ ] **9.3.1** Test with real Twitter API (sandbox)
- [ ] **9.3.2** Test search query building
- [ ] **9.3.3** Test result parsing
- [ ] **9.3.4** Test pagination
- [ ] **9.3.5** Test rate limiting
- [ ] **9.3.6** Test error responses

### 9.4 BlueSky Integration Tests (v0.1)
- [ ] **9.4.1** Test BlueSky authentication
- [ ] **9.4.2** Test search functionality
- [ ] **9.4.3** Test result parsing
- [ ] **9.4.4** Test error handling

---

## Phase 10: Performance Testing

### 10.1 Latency Tests
- [ ] **10.1.1** Measure cache lookup time
- [ ] **10.1.2** Measure extraction time
- [ ] **10.1.3** Measure search query building time
- [ ] **10.1.4** Measure API response time
- [ ] **10.1.5** Measure processing time
- [ ] **10.1.6** Measure end-to-end latency
- [ ] **10.1.7** Set performance benchmarks

### 10.2 Throughput Tests
- [ ] **10.2.1** Test concurrent request handling
- [ ] **10.2.2** Measure requests per second
- [ ] **10.2.3** Test queue management
- [ ] **10.2.4** Identify bottlenecks

### 10.3 Resource Usage
- [ ] **10.3.1** Profile memory usage
- [ ] **10.3.2** Profile CPU usage
- [ ] **10.3.3** Identify memory leaks
- [ ] **10.3.4** Optimize resource usage

### 10.4 Load Testing
- [ ] **10.4.1** Simulate high request volume
- [ ] **10.4.2** Test graceful degradation
- [ ] **10.4.3** Test error rate under load
- [ ] **10.4.4** Document performance characteristics

---

## Phase 11: API Layer

### 11.1 FastAPI Routes
- [ ] **11.1.1** Create FastAPI application
- [ ] **11.1.2** Create `/check-claim` POST endpoint
  - [ ] Parse request body
  - [ ] Call pipeline
  - [ ] Format response
  - [ ] Handle errors
- [ ] **11.1.3** Create `/health` GET endpoint
- [ ] **11.1.4** Create `/status` GET endpoint (optional)
- [ ] **11.1.5** Implement request validation
- [ ] **11.1.6** Implement error responses
- [ ] **11.1.7** Add OpenAPI documentation

### 11.2 Authentication & Authorization
- [ ] **11.2.1** Implement API key authentication
- [ ] **11.2.2** Implement rate limiting
- [ ] **11.2.3** Implement user tracking
- [ ] **11.2.4** Test auth and rate limiting

### 11.3 API Testing
- [ ] **11.3.1** Test endpoint creation
- [ ] **11.3.2** Test request/response validation
- [ ] **11.3.3** Test error responses
- [ ] **11.3.4** Test rate limiting
- [ ] **11.3.5** Test concurrent requests
- [ ] **11.3.6** Load test API

---

## Phase 12: Deployment & DevOps

### 12.1 Containerization
- [ ] **12.1.1** Create Dockerfile
- [ ] **12.1.2** Create docker-compose.yml
- [ ] **12.1.3** Test Docker build
- [ ] **12.1.4** Create Docker registry push

### 12.2 AWS Lambda (if applicable)
- [ ] **12.2.1** Create Lambda handler
- [ ] **12.2.2** Setup Lambda environment variables
- [ ] **12.2.3** Test Lambda locally
- [ ] **12.2.4** Deploy to AWS Lambda

### 12.3 CI/CD Pipeline
- [ ] **12.3.1** Setup GitHub Actions workflows
- [ ] **12.3.2** Run linting on PR
- [ ] **12.3.3** Run tests on PR
- [ ] **12.3.4** Generate coverage reports
- [ ] **12.3.5** Deploy on merge to main
- [ ] **12.3.6** Setup rollback mechanism

### 12.4 Monitoring & Logging
- [ ] **12.4.1** Setup centralized logging (CloudWatch/ELK)
- [ ] **12.4.2** Setup metrics collection
- [ ] **12.4.3** Setup alerting
- [ ] **12.4.4** Setup error tracking (Sentry)
- [ ] **12.4.5** Create dashboards

---

## Phase 13: Documentation

### 13.1 Code Documentation
- [ ] **13.1.1** Add docstrings to all modules
- [ ] **13.1.2** Add type hint documentation
- [ ] **13.1.3** Add inline comments for complex logic
- [ ] **13.1.4** Generate API documentation

### 13.2 User Documentation
- [ ] **13.2.1** Write setup guide
- [ ] **13.2.2** Write usage guide
- [ ] **13.2.3** Write configuration guide
- [ ] **13.2.4** Write troubleshooting guide
- [ ] **13.2.5** Create API documentation
- [ ] **13.2.6** Create architecture diagrams

### 13.3 Developer Documentation
- [ ] **13.3.1** Write development setup guide
- [ ] **13.3.2** Write testing guide
- [ ] **13.3.3** Write contribution guidelines
- [ ] **13.3.4** Create module documentation
- [ ] **13.3.5** Document design decisions

---

## Phase 14: Version 0.1 Features & LLM System Enhancements

### 14.1 LLM Configuration System - Phase 2 (Enhancement)
- [ ] **14.1.1** YAML config file support
  - [ ] Create `config/llm_configs.yaml` for runtime configuration
  - [ ] Implement YAML parser and loader
  - [ ] Allow environment variable overrides in config
  - [ ] Support config hot-reload without restart
- [ ] **14.1.2** Pydantic models for configuration validation
  - [ ] Define `UseCase` Pydantic model
  - [ ] Define `ProviderConfig` Pydantic model
  - [ ] Add schema validation for all configs
  - [ ] Generate JSON schema from models
- [ ] **14.1.3** Additional LLM provider support
  - [ ] Implement `OpenAIProvider`
  - [ ] Implement `AnthropicProvider`
  - [ ] Add provider auto-detection and fallback
  - [ ] Support provider switching without code changes
- [ ] **14.1.4** Cost tracking and usage monitoring
  - [ ] Track tokens used per LLM call
  - [ ] Calculate costs based on provider pricing
  - [ ] Aggregate usage by use case and time period
  - [ ] Generate usage reports and cost analysis
- [ ] **14.1.5** Model capability querying
  - [ ] Cache live model lists from providers
  - [ ] Detect deprecated/removed models
  - [ ] Query parameter ranges and limits for models
  - [ ] Alert on breaking changes

### 14.2 Advanced Claim Analysis
- [ ] **14.2.1** Implement semantic similarity scoring
- [ ] **14.2.2** Implement negation handling
- [ ] **14.2.3** Implement temporal logic
- [ ] **14.2.4** Add specialized processors for claim types

### 14.3 BlueSky Support
- [ ] **14.3.1** Complete BlueSkySearcher implementation
- [ ] **14.3.2** Test BlueSky integration
- [ ] **14.3.3** Add configuration for BlueSky

### 14.4 Iterative Query Expansion
- [ ] **14.4.1** Implement iterative LLM-based search strategy
- [ ] **14.4.2** Implement cost-aware query building (Phase 1.4)
- [ ] **14.4.3** Test query expansion logic
- [ ] **14.4.4** Benchmark cost savings

---

## Priority Legend

- **High Priority** (Phase 0-6): Core functionality, required for MVP
- **Medium Priority** (Phase 7-9): Testing and quality assurance
- **Low Priority** (Phase 10-14): Optimization, advanced features, v0.1+ roadmap

---

## Testing Coverage Goals

| Module | Target Coverage | Current |
|--------|-----------------|---------|
| `core/models.py` | 95% | 0% |
| `core/interfaces.py` | 90% | 0% |
| `logging_config.py` | 90% | 0% |
| `extractors/text_extractor.py` | 95% | 0% |
| `extractors/image_extractor.py` | 95% | 0% |
| `searchers/twitter_searcher.py` | 85% | 0% |
| `searchers/bluesky_searcher.py` | 85% | 0% |
| `processors/result_analyzer.py` | 90% | 0% |
| `processors/response_generator.py` | 90% | 0% |
| `storage/cache.py` | 95% | 0% |
| `storage/database.py` | 90% | 0% |
| `pipeline/factcheck_pipeline.py` | 85% | 0% |
| **Overall** | **90%** | **0%** |

---

## Quick Reference: Run Commands

```bash
# Setup
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v
pytest src/factchecker/ -v  # Module tests only
pytest src/factchecker/extractors/tests/ -v  # Specific module

# Coverage
pytest --cov=src/factchecker --cov-report=html

# Lint
ruff check .
mypy --strict src/

# Format
ruff format .

# Test specific function
pytest src/factchecker/extractors/tests/test_text_extractor.py::test_text_extraction_basic -v
pytest src/factchecker/tests/test_pipeline.py::test_pipeline_initialization -v
# RUN WITH VERBOSE OUTPUT AND LOGGING:
pytest src/factchecker/tests/test_pipeline.py -v -s --log-cli-level=INFO
# To debug a single test: set breakpoints, then select the test name in the editor, then select debug configuration 'Python: Debug Test by Name'.
```

---

## Notes

- Use `@pytest.mark.asyncio` for async tests
- Use `AsyncMock` for mocking async functions
- All tests should be independent and idempotent
- Update this file as tasks are completed
- Update coverage table after each testing phase
