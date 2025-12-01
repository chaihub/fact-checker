"""Component-level tests for FactCheckPipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from factchecker.pipeline.factcheck_pipeline import FactCheckPipeline
from factchecker.core.models import (
    FactCheckRequest,
    FactCheckResponse,
    ExtractedClaim,
    VerdictEnum,
)
from factchecker.core.interfaces import IPipeline
from factchecker.tests.fixtures import (
    sample_request,
    sample_response,
    sample_extracted_claim,
    sample_search_results,
)


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def mock_extractors():
    return AsyncMock()


@pytest.fixture
def mock_searchers():
    return AsyncMock()


@pytest.fixture
def mock_processors():
    return AsyncMock()


@pytest.fixture
def pipeline(mock_cache, mock_extractors, mock_searchers, mock_processors):
    return FactCheckPipeline(
        cache=mock_cache,
        extractors=mock_extractors,
        searchers=mock_searchers,
        processors=mock_processors,
    )


@pytest.mark.asyncio
async def test_pipeline_initialization(pipeline):
    """Test pipeline initializes correctly."""
    assert pipeline.cache is not None
    assert pipeline.extractors is not None
    assert pipeline.searchers is not None
    assert pipeline.processors is not None


@pytest.mark.asyncio
async def test_pipeline_implements_ipipeline():
    """Test that FactCheckPipeline implements IPipeline interface."""
    mock_cache = AsyncMock()
    mock_extractors = AsyncMock()
    mock_searchers = AsyncMock()
    mock_processors = AsyncMock()
    
    pipeline = FactCheckPipeline(
        cache=mock_cache,
        extractors=mock_extractors,
        searchers=mock_searchers,
        processors=mock_processors,
    )
    
    assert isinstance(pipeline, IPipeline)
    assert hasattr(pipeline, "check_claim")
    assert callable(pipeline.check_claim)


@pytest.mark.asyncio
async def test_pipeline_cache_hit(pipeline, mock_cache, sample_request, sample_response):
    """Test that cached results are returned."""
    mock_cache.get.return_value = sample_response

    response = await pipeline.check_claim(sample_request)

    assert response.cached is True
    mock_cache.get.assert_called()


@pytest.mark.asyncio
async def test_pipeline_requires_input_validation(pipeline, sample_request):
    """Test that pipeline validates input."""
    # Validation should fail at model creation time
    with pytest.raises(ValueError, match="At least one of claim_text or image_data"):
        FactCheckRequest(
            claim_text=None, image_data=None, user_id="test"
        )


@pytest.mark.asyncio
async def test_pipeline_full_flow_with_mocks(
    pipeline, mock_cache, mock_extractors, sample_request, sample_extracted_claim
):
    """Test complete pipeline flow with mock implementations."""
    # Setup mocks
    mock_cache.get.return_value = None  # Cache miss
    mock_extractors.extract.return_value = sample_extracted_claim

    # Execute pipeline
    response = await pipeline.check_claim(sample_request)

    # Verify response structure
    assert isinstance(response, FactCheckResponse)
    assert response.request_id is not None
    assert response.claim_id is not None
    assert response.verdict in [
        VerdictEnum.AUTHENTIC,
        VerdictEnum.NOT_AUTHENTIC,
        VerdictEnum.MIXED,
        VerdictEnum.UNCLEAR,
    ]
    assert isinstance(response.confidence, float)
    assert 0.0 <= response.confidence <= 1.0
    assert isinstance(response.explanation, str)
    assert len(response.explanation) > 0
    assert isinstance(response.evidence, list)
    assert isinstance(response.references, list)
    assert isinstance(response.processing_time_ms, float)
    assert response.processing_time_ms >= 0
    assert response.cached is False


@pytest.mark.asyncio
async def test_pipeline_mock_search_params(pipeline, sample_extracted_claim):
    """Test that _build_search_params returns valid structure."""
    params = await pipeline._build_search_params(sample_extracted_claim)

    assert isinstance(params, dict)
    assert "query" in params
    assert "limit" in params
    assert params["query"] == sample_extracted_claim.claim_text
    assert params["limit"] == 5


@pytest.mark.asyncio
async def test_pipeline_mock_search_results(pipeline, sample_extracted_claim):
    """Test that _search_sources returns properly typed SearchResult objects."""
    params = {"query": "test", "limit": 5}
    results = await pipeline._search_sources(sample_extracted_claim, params)

    assert isinstance(results, list)
    assert len(results) > 0

    for result in results:
        assert hasattr(result, "platform")
        assert hasattr(result, "content")
        assert hasattr(result, "author")
        assert hasattr(result, "url")
        assert hasattr(result, "timestamp")
        assert isinstance(result.platform, str)
        assert isinstance(result.content, str)
        assert isinstance(result.author, str)
        assert isinstance(result.url, str)


@pytest.mark.asyncio
async def test_pipeline_mock_response_generation(
    pipeline, sample_request, sample_extracted_claim
):
    """Test that _generate_response returns properly constructed FactCheckResponse."""
    start_time = datetime.now()
    mock_results = []

    response = await pipeline._generate_response(
        sample_request, sample_extracted_claim, mock_results, start_time
    )

    assert isinstance(response, FactCheckResponse)
    assert response.request_id is not None
    assert response.claim_id is not None
    assert isinstance(response.verdict, VerdictEnum)
    assert isinstance(response.confidence, float)
    assert 0.0 <= response.confidence <= 1.0
    assert isinstance(response.explanation, str)
    assert len(response.explanation) > 0
    assert isinstance(response.evidence, list)
    assert isinstance(response.references, list)
    assert isinstance(response.search_queries_used, list)
    assert isinstance(response.processing_time_ms, float)
    assert response.processing_time_ms >= 0


@pytest.mark.asyncio
async def test_pipeline_response_has_all_required_fields(
    pipeline, sample_request, sample_extracted_claim
):
    """Test that response includes all required VerdictEnum values."""
    start_time = datetime.now()
    response = await pipeline._generate_response(
        sample_request, sample_extracted_claim, [], start_time
    )

    # Verify all fields from FactCheckResponse model
    required_fields = [
        "request_id",
        "claim_id",
        "verdict",
        "confidence",
        "evidence",
        "references",
        "explanation",
        "search_queries_used",
        "cached",
        "processing_time_ms",
        "timestamp",
    ]

    for field in required_fields:
        assert hasattr(response, field), f"Response missing field: {field}"
        assert getattr(response, field) is not None or field == "evidence"
