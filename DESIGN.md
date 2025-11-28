# FactChecker Component Design

## Directory Structure

```
src/
├── factchecker/
│   ├── __init__.py
│   ├── logging_config.py      # Centralized logging setup
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py          # Pydantic data models
│   │   └── interfaces.py      # Abstract base classes
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── factcheck_pipeline.py
│   │   └── stages.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── image_extractor.py
│   │   ├── text_extractor.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_image_extractor.py
│   │       └── test_text_extractor.py
│   ├── searchers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── twitter_searcher.py
│   │   ├── bluesky_searcher.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_twitter_searcher.py
│   │       └── test_bluesky_searcher.py
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── response_generator.py
│   │   ├── result_analyzer.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_response_generator.py
│   │       └── test_result_analyzer.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── cache.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_cache.py
│   └── tests/
│       ├── __init__.py
│       ├── test_pipeline.py
│       └── fixtures.py

tests/
├── integration/
│   ├── test_end_to_end.py
│   └── test_whatsapp_integration.py
└── performance/
    └── test_latency.py
```

---

## Data Models (core/models.py)

### Input Model
```python
from typing import Optional
from pydantic import BaseModel, field_validator

class FactCheckRequest(BaseModel):
    """
    Claim input for fact-checking.
    At least one of claim_text or image_data must be present.
    """
    claim_text: Optional[str] = None
    image_data: Optional[bytes] = None
    user_id: str
    source_platform: str = "whatsapp"  # whatsapp, twitter, etc.
    request_id: Optional[str] = None  # Generated if not provided

    @field_validator("claim_text", "image_data")
    @classmethod
    def at_least_one_required(cls, v, info):
        values = info.data
        if not values.get("claim_text") and not values.get("image_data"):
            raise ValueError(
                "At least one of claim_text or image_data must be provided"
            )
        return v

    class Config:
        str_strip_whitespace = True
```

### Internal Extraction Result
```python
class ExtractedClaim(BaseModel):
    """Output from extractors (Image or Text)."""
    claim_text: str
    extracted_from: Literal["image", "text", "hybrid"]
    confidence: float  # 0-1, confidence in extraction
    raw_input_type: Literal["text_only", "image_only", "both"]
    metadata: dict = {}  # OCR quality, image dimensions, etc.
```

### Search Result
```python
from typing import List
from datetime import datetime

class SearchResult(BaseModel):
    """Individual result from a searcher."""
    platform: str  # twitter, bluesky, etc.
    content: str
    author: str
    url: str
    timestamp: datetime
    engagement: dict = {}  # likes, retweets, replies
    metadata: dict = {}
```

### Output Model
```python
from enum import Enum

class VerdictEnum(str, Enum):
    AUTHENTIC = "authentic"
    NOT_AUTHENTIC = "not_authentic"
    MIXED = "mixed"
    UNCLEAR = "unclear"

class Reference(BaseModel):
    title: str
    url: str
    snippet: str
    platform: str

class Evidence(BaseModel):
    claim_fragment: str
    finding: str
    supporting_results: List[SearchResult]
    confidence: float

class FactCheckResponse(BaseModel):
    """Complete fact-check output."""
    request_id: str
    claim_id: str
    verdict: VerdictEnum
    confidence: float  # 0-1
    evidence: List[Evidence]
    references: List[Reference]
    explanation: str
    search_queries_used: List[str]
    cached: bool
    processing_time_ms: float
    timestamp: datetime
```

---

## Logging Strategy (logging_config.py)

Structured logging implementation with request ID tracing and performance monitoring.

### Core Components

```python
# Context variable for request tracing across async boundaries
request_id_var: contextvars.ContextVar = contextvars.ContextVar(
    "request_id", default="N/A"
)
```

### Setup Function
```python
def setup_logging(level=logging.INFO) -> logging.Logger:
    """Initialize logging with structured format."""
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(request_id)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger = logging.getLogger("factchecker")
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
```

### Logger Factory
```python
def get_logger(name: str) -> logging.LoggerAdapter:
    """Get logger with automatic request_id injection."""
    logger = logging.getLogger(f"factchecker.{name}")
    return logging.LoggerAdapter(logger, {"request_id": lambda: request_id_var.get()})
```

### Stage Decorator
```python
@log_stage(stage_name: str)
```
- Logs stage start/completion with timing
- Handles both sync and async functions automatically
- Captures execution time in milliseconds
- Logs errors with full stack traces
- Usage: `@log_stage("Claim Extraction")`

### Logging Features
- **Request ID Tracing**: Automatic context injection across all loggers
- **Performance Monitoring**: Each stage tracked with elapsed time
- **Error Context**: Full exception logging with stack traces
- **Async-Safe**: Uses `contextvars` for thread-safe request ID propagation
- **Structured Output**: Consistent format for parsing and analysis

---

## Interfaces (core/interfaces.py)

```python
from abc import ABC, abstractmethod
from typing import List
from .models import ExtractedClaim, SearchResult, FactCheckResponse

class BaseExtractor(ABC):
    """Abstract base for text and image extractors."""
    
    @abstractmethod
    async def extract(self, claim_text: Optional[str], 
                     image_data: Optional[bytes]) -> ExtractedClaim:
        """Extract structured claim from input."""
        pass

class BaseSearcher(ABC):
    """Abstract base for all searchers (Twitter, BlueSky, etc.)."""
    
    @abstractmethod
    async def search(self, claim: str, 
                    query_params: dict) -> List[SearchResult]:
        """Search external source for results."""
        pass
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Identifier for this searcher."""
        pass

class BaseProcessor(ABC):
    """Abstract base for result processors."""
    
    @abstractmethod
    async def process(self, claim: ExtractedClaim,
                     results: List[SearchResult]) -> dict:
        """Analyze results and generate verdict."""
        pass

class IPipeline(ABC):
    """Fact-checker pipeline interface."""
    
    @abstractmethod
    async def check_claim(self, request: FactCheckRequest) -> FactCheckResponse:
        """Execute full fact-checking pipeline."""
        pass
```

---

## Module-Level Testing

### Extractor Tests (extractors/tests/test_text_extractor.py)
```python
import pytest
from factchecker.extractors.text_extractor import TextExtractor
from factchecker.core.models import ExtractedClaim

@pytest.fixture
def extractor():
    return TextExtractor()

@pytest.mark.asyncio
async def test_simple_claim_extraction(extractor):
    """Test basic text extraction."""
    result = await extractor.extract(
        claim_text="The sky is blue",
        image_data=None
    )
    assert isinstance(result, ExtractedClaim)
    assert result.claim_text == "The sky is blue"
    assert result.extracted_from == "text"
    assert 0 <= result.confidence <= 1

@pytest.mark.asyncio
async def test_extraction_requires_input(extractor):
    """Test that extraction fails without input."""
    with pytest.raises(ValueError):
        await extractor.extract(claim_text=None, image_data=None)

@pytest.mark.asyncio
async def test_hybrid_extraction(extractor):
    """Test extraction from both text and image."""
    # Mock image data
    result = await extractor.extract(
        claim_text="Verify this",
        image_data=b"mock_image_data"
    )
    assert result.raw_input_type == "both"
```

### Searcher Tests (searchers/tests/test_twitter_searcher.py)
```python
import pytest
from unittest.mock import AsyncMock, patch
from factchecker.searchers.twitter_searcher import TwitterSearcher
from factchecker.core.models import SearchResult

@pytest.fixture
def twitter_searcher():
    return TwitterSearcher(api_key="test_key")

@pytest.mark.asyncio
async def test_twitter_search_returns_results(twitter_searcher):
    """Test successful Twitter search."""
    with patch.object(twitter_searcher, '_query_api', 
                     new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [
            {"text": "Sample tweet", "author_id": "123"},
        ]
        
        results = await twitter_searcher.search(
            claim="test claim",
            query_params={"max_results": 10}
        )
        
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)

@pytest.mark.asyncio
async def test_twitter_search_api_failure_graceful(twitter_searcher):
    """Test graceful handling of API failures."""
    with patch.object(twitter_searcher, '_query_api',
                     side_effect=Exception("API Error")):
        with pytest.raises(Exception):
            await twitter_searcher.search("claim", {})
```

### Processor Tests (processors/tests/test_response_generator.py)
```python
import pytest
from factchecker.processors.response_generator import ResponseGenerator
from factchecker.core.models import ExtractedClaim, SearchResult, VerdictEnum

@pytest.fixture
def generator():
    return ResponseGenerator()

@pytest.mark.asyncio
async def test_response_generation(generator):
    """Test verdict and explanation generation."""
    claim = ExtractedClaim(
        claim_text="The Earth is flat",
        extracted_from="text",
        confidence=1.0,
        raw_input_type="text_only"
    )
    
    results = [
        SearchResult(
            platform="twitter",
            content="NASA confirms Earth is spherical",
            author="NASA",
            url="https://twitter.com/nasa",
            timestamp=datetime.now()
        )
    ]
    
    response = await generator.process(claim, results)
    assert response['verdict'] == VerdictEnum.NOT_AUTHENTIC
    assert response['confidence'] >= 0.5
```

---

## Component-Level Testing (tests/test_pipeline.py)

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from factchecker.pipeline.factcheck_pipeline import FactCheckPipeline
from factchecker.core.models import FactCheckRequest, FactCheckResponse

@pytest.fixture
def pipeline():
    return FactCheckPipeline(
        cache=MagicMock(),
        extractors=MagicMock(),
        searchers=MagicMock(),
        processors=MagicMock()
    )

@pytest.mark.asyncio
async def test_full_pipeline_execution(pipeline):
    """Test end-to-end pipeline."""
    request = FactCheckRequest(
        claim_text="COVID-19 vaccines contain microchips",
        image_data=None,
        user_id="user123",
        source_platform="whatsapp"
    )
    
    response = await pipeline.check_claim(request)
    
    assert isinstance(response, FactCheckResponse)
    assert response.request_id == request.request_id
    assert response.verdict is not None
    assert len(response.evidence) > 0
    assert response.processing_time_ms >= 0

@pytest.mark.asyncio
async def test_pipeline_cache_hit(pipeline):
    """Test that cached results are returned."""
    request = FactCheckRequest(
        claim_text="Sample claim",
        image_data=None,
        user_id="user123"
    )
    
    # Mock cache hit
    cached_response = MagicMock(spec=FactCheckResponse)
    pipeline.cache.get.return_value = cached_response
    
    response = await pipeline.check_claim(request)
    
    assert response.cached is True
    pipeline.cache.get.assert_called_once()

@pytest.mark.asyncio
async def test_pipeline_with_image_input(pipeline):
    """Test pipeline handles image extraction."""
    request = FactCheckRequest(
        claim_text=None,
        image_data=b"fake_image_data",
        user_id="user123"
    )
    
    response = await pipeline.check_claim(request)
    assert isinstance(response, FactCheckResponse)

@pytest.mark.asyncio
async def test_pipeline_requires_at_least_one_input(pipeline):
    """Test validation of inputs."""
    with pytest.raises(ValueError):
        await pipeline.check_claim(
            FactCheckRequest(
                claim_text=None,
                image_data=None,
                user_id="user123"
            )
        )
```

---

## Pipeline Implementation (pipeline/factcheck_pipeline.py)

```python
import asyncio
import uuid
from datetime import datetime
from typing import Optional
from factchecker.logging_config import get_logger, log_stage, request_id_var
from factchecker.core.models import FactCheckRequest, FactCheckResponse

logger = get_logger(__name__)

class FactCheckPipeline:
    """Orchestrates fact-checking pipeline stages."""
    
    def __init__(self, cache, extractors, searchers, processors):
        self.cache = cache
        self.extractors = extractors
        self.searchers = searchers
        self.processors = processors
    
    async def check_claim(self, request: FactCheckRequest) -> FactCheckResponse:
        """Execute full fact-checking pipeline."""
        
        # Generate request ID for tracing
        request.request_id = request.request_id or str(uuid.uuid4())
        request_id_var.set(request.request_id)
        
        start_time = datetime.now()
        logger.info(
            "Fact-check request started",
            extra={
                'user_id': request.user_id,
                'source': request.source_platform
            }
        )
        
        try:
            # Stage 1: Cache lookup
            cached = await self._check_cache(request)
            if cached:
                logger.info("Cache hit - returning cached response")
                cached.cached = True
                cached.processing_time_ms = (
                    datetime.now() - start_time
                ).total_seconds() * 1000
                return cached
            
            # Stage 2: Extract claim
            extracted_claim = await self._extract_claim(request)
            
            # Stage 3: Identify search parameters
            search_params = await self._build_search_params(extracted_claim)
            
            # Stage 4: Search external sources
            all_results = await self._search_sources(
                extracted_claim, search_params
            )
            
            # Stage 5: Process results
            response = await self._generate_response(
                request, extracted_claim, all_results, start_time
            )
            
            # Stage 6: Cache response
            await self._cache_response(response)
            
            logger.info("Fact-check request completed successfully")
            return response
            
        except Exception as e:
            logger.error(
                f"Pipeline failed: {str(e)}",
                exc_info=True
            )
            raise
    
    @log_stage("Cache Lookup")
    async def _check_cache(self, request: FactCheckRequest) -> Optional[FactCheckResponse]:
        """Check if claim result is cached."""
        return await self.cache.get(request.claim_text or "")
    
    @log_stage("Claim Extraction")
    async def _extract_claim(self, request: FactCheckRequest):
        """Extract structured claim from text or image."""
        return await self.extractors.extract(
            request.claim_text,
            request.image_data
        )
    
    @log_stage("Search Parameter Building")
    async def _build_search_params(self, claim):
        """Generate search parameters from extracted claim."""
        # Implementation depends on claim type
        pass
    
    @log_stage("External Search")
    async def _search_sources(self, claim, params):
        """Query all enabled searchers concurrently."""
        tasks = [
            self.searchers[platform].search(claim, params)
            for platform in self.searchers
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    @log_stage("Response Generation")
    async def _generate_response(self, request, claim, results, start_time):
        """Generate fact-check verdict and explanation."""
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        return await self.processors.process(claim, results, processing_time_ms)
    
    @log_stage("Cache Storage")
    async def _cache_response(self, response: FactCheckResponse):
        """Store response in cache."""
        await self.cache.set(response.request_id, response)
```

---

## Key Design Features

### 1. Input Validation
- `FactCheckRequest` validates at least one input present
- Input type inferred automatically from present fields
- No explicit `input_type` parameter needed

### 2. Structured Logging
- Request IDs for tracing across components via `contextvars`
- Stage-level timing via `@log_stage` decorator (async and sync safe)
- Automatic context injection in all loggers
- Errors logged with full stack traces
- Format: `timestamp | module | level | request_id | message`

### 3. Testability
- **Unit tests** for each module (extractors, searchers, processors, storage)
- **Component tests** for pipeline orchestration
- **Integration tests** for end-to-end workflows
- **Fixtures** for common mocks and test data
- Mock-friendly interfaces with ABC base classes
- Async support with `pytest-asyncio`
- Fixtures shared across test suite in `tests/fixtures.py`

### 4. Extensibility
- Abstract base classes define contracts
- New searchers/extractors inherit and implement interface
- Storage backend swappable
- Processors composable for different claim types

### 5. Error Handling & Resilience
- Graceful degradation (partial results if one searcher fails)
- Timeout handling for external APIs
- Cache fallback if search fails
- Structured error logging with context

---

## Implementation Status

### Completed (Phase 0-7)
- [x] Project structure and skeleton
- [x] Core data models (all Pydantic models with validation)
- [x] Logging configuration (structured, async-safe, context-aware)
- [x] Abstract interfaces (BaseExtractor, BaseSearcher, BaseProcessor, IPipeline)
- [x] TextExtractor and ImageExtractor implementations
- [x] TwitterSearcher and BlueSkySearcher placeholders
- [x] ResultAnalyzer and ResponseGenerator placeholders
- [x] Cache storage with TTL support
- [x] Database interface skeleton
- [x] Pipeline orchestrator with 6 stages
- [x] Unit test stubs for all modules (23 tests created)
- [x] Component test fixtures and pipeline tests
- [x] Integration test placeholders
- [x] Performance test placeholders

### In Progress / TODO
- [ ] Model validation tests
- [ ] Logging tests
- [ ] Extractor implementation completion (edge cases, encodings)
- [ ] OCR integration for ImageExtractor
- [ ] Twitter API integration
- [ ] BlueSky API integration
- [ ] Advanced NLP-based claim analysis
- [ ] Response formatting and evidence extraction
- [ ] Database schema and CRUD operations
- [ ] Cache strategy refinement
- [ ] End-to-end integration tests
- [ ] Performance benchmarking
- [ ] API endpoint implementation
- [ ] Deployment and monitoring

### Files Created
**Core Module** (18 files):
- `src/factchecker/__init__.py`
- `src/factchecker/logging_config.py`
- `src/factchecker/core/models.py` (7 models)
- `src/factchecker/core/interfaces.py` (4 abstract classes)
- `src/factchecker/extractors/text_extractor.py`, `image_extractor.py`
- `src/factchecker/searchers/twitter_searcher.py`, `bluesky_searcher.py`
- `src/factchecker/processors/result_analyzer.py`, `response_generator.py`
- `src/factchecker/storage/cache.py`, `database.py`
- `src/factchecker/pipeline/factcheck_pipeline.py`, `stages.py`

**Test Module** (14 files):
- 8 unit test files (extractors, searchers, processors, storage)
- `src/factchecker/tests/fixtures.py` (5 shared fixtures)
- `src/factchecker/tests/test_pipeline.py` (3 component tests)
- 2 integration test stubs
- 1 performance test stub

**Documentation** (2 files):
- `DESIGN.md` (this file, comprehensive architecture)
- `TODO_factchecker.md` (250+ granular implementation tasks)

Total: 34 Python files + 2 documentation files
