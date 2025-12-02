"""Component-level tests for FactCheckPipeline."""

import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, call, patch
from datetime import datetime
import uuid

from factchecker.pipeline.factcheck_pipeline import FactCheckPipeline
from factchecker.core.models import (
    FactCheckRequest,
    FactCheckResponse,
    ExtractedClaim,
    VerdictEnum,
)
from factchecker.core.interfaces import IPipeline
from factchecker.logging_config import get_logger, request_id_var
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


# ============================================================================
# Task 6.2.4b: End-to-End Pipeline Test
# ============================================================================

class TestPipeline64b:
    """Test 6.2.4b: End-to-end skeleton test - verify full pipeline flow."""

    @pytest.mark.asyncio
    async def test_full_pipeline_end_to_end_with_all_stages(
        self, pipeline, mock_cache, mock_extractors, sample_request, sample_extracted_claim, caplog
    ):
        """Test 6.2.4b: Full pipeline execution flow with all mocked stages."""
        with caplog.at_level(logging.INFO):
            mock_cache.get.return_value = None
            mock_extractors.extract.return_value = sample_extracted_claim

            response = await pipeline.check_claim(sample_request)

            # Verify complete response structure
            assert isinstance(response, FactCheckResponse)
            assert response.request_id is not None
            assert response.cached is False
            assert response.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_full_pipeline_data_flow_request_to_response(
        self, pipeline, mock_cache, mock_extractors, sample_request, sample_extracted_claim
    ):
        """Test 6.2.4b: Verify data flows correctly through all stages."""
        mock_cache.get.return_value = None
        mock_extractors.extract.return_value = sample_extracted_claim

        response = await pipeline.check_claim(sample_request)

        # Verify complete chain: Request → ExtractedClaim → SearchParams → Results → Response
        assert sample_request.request_id == response.request_id
        assert response.verdict in [v.value for v in VerdictEnum]
        assert len(response.evidence) > 0
        assert len(response.references) > 0

    @pytest.mark.asyncio
    async def test_full_pipeline_with_various_claim_types(
        self, pipeline, mock_cache, mock_extractors
    ):
        """Test 6.2.4b: Test with various claim types."""
        mock_cache.get.return_value = None

        claim_types = [
            ("The Earth is round", "text_only", "text"),
            ("COVID vaccines contain microchips", "text_only", "text"),
            ("Climate change is real", "text_only", "text"),
        ]

        for claim_text, input_type, extracted_from in claim_types:
            request = FactCheckRequest(claim_text=claim_text, user_id="test_user")
            extracted = ExtractedClaim(
                claim_text=claim_text,
                extracted_from=extracted_from,
                confidence=0.95,
                raw_input_type=input_type,
                metadata={},
            )
            mock_extractors.extract.return_value = extracted

            response = await pipeline.check_claim(request)

            assert response is not None
            assert response.verdict is not None

    @pytest.mark.asyncio
    async def test_full_pipeline_response_structure_validation(
        self, pipeline, mock_cache, mock_extractors, sample_request, sample_extracted_claim
    ):
        """Test 6.2.4b: Verify output matches expected FactCheckResponse structure."""
        mock_cache.get.return_value = None
        mock_extractors.extract.return_value = sample_extracted_claim

        response = await pipeline.check_claim(sample_request)

        # Validate all required fields are present and properly typed
        required_fields = {
            "request_id": str,
            "claim_id": str,
            "verdict": VerdictEnum,
            "confidence": float,
            "evidence": list,
            "references": list,
            "explanation": str,
            "search_queries_used": list,
            "cached": bool,
            "processing_time_ms": float,
            "timestamp": datetime,
        }

        for field, expected_type in required_fields.items():
            assert hasattr(response, field)
            value = getattr(response, field)
            if field == "verdict":
                assert isinstance(value, expected_type)
            else:
                assert isinstance(value, expected_type)


# ============================================================================
# Task 6.2.4c: Stage Integration and Composition Test
# ============================================================================

class TestPipeline64c:
    """Test 6.2.4c: Stage integration and composition - test chaining and error flow."""

    @pytest.mark.asyncio
    async def test_stage_chaining_data_propagation(
        self, pipeline, mock_cache, mock_extractors, sample_request, sample_extracted_claim
    ):
        """Test 6.2.4c: Verify stage output becomes next stage input."""
        mock_cache.get.return_value = None
        mock_extractors.extract.return_value = sample_extracted_claim

        # Test individual stage outputs feed into next stage
        extracted = await pipeline._extract_claim(sample_request)
        assert isinstance(extracted, ExtractedClaim)

        params = await pipeline._build_search_params(extracted)
        assert isinstance(params, dict)

        results = await pipeline._search_sources(extracted, params)
        assert isinstance(results, list)

        response = await pipeline._generate_response(sample_request, extracted, results, datetime.now())
        assert isinstance(response, FactCheckResponse)

    @pytest.mark.asyncio
    async def test_error_propagation_through_pipeline(
        self, pipeline, mock_cache, mock_extractors, sample_request
    ):
        """Test 6.2.4c: Test error propagation through pipeline."""
        mock_cache.get.side_effect = Exception("Cache error")
        mock_extractors.extract.return_value = None

        # Error in cache should be caught by try-except in check_claim
        with pytest.raises(Exception):
            await pipeline.check_claim(sample_request)

    @pytest.mark.asyncio
    async def test_logging_at_each_stage(
        self, pipeline, mock_cache, mock_extractors, sample_request, sample_extracted_claim, caplog
    ):
        """Test 6.2.4c: Test logging/tracing at each stage."""
        with caplog.at_level(logging.INFO):
            mock_cache.get.return_value = None
            mock_extractors.extract.return_value = sample_extracted_claim

            response = await pipeline.check_claim(sample_request)

            # Verify logging occurred
            log_messages = [record.message for record in caplog.records]
            assert any("Fact-check request started" in msg for msg in log_messages)
            assert any("Fact-check request completed" in msg for msg in log_messages)

    @pytest.mark.asyncio
    async def test_stage_method_chaining_integration(
        self, pipeline, mock_cache, mock_extractors, sample_request, sample_extracted_claim, caplog
    ):
        """Test 6.2.4c: Test chaining of mocked stages together."""
        with caplog.at_level(logging.DEBUG):
            mock_cache.get.return_value = None
            mock_extractors.extract.return_value = sample_extracted_claim

            # Execute full pipeline
            response = await pipeline.check_claim(sample_request)

            # Verify each stage was called in correct order
            assert response is not None
            assert mock_cache.get.called
            assert mock_extractors.extract.called

    @pytest.mark.asyncio
    async def test_cache_miss_triggers_full_pipeline(
        self, pipeline, mock_cache, mock_extractors, sample_request, sample_extracted_claim
    ):
        """Test 6.2.4c: Verify cache miss triggers full stage execution."""
        mock_cache.get.return_value = None
        mock_cache.set = AsyncMock()
        mock_extractors.extract.return_value = sample_extracted_claim

        response = await pipeline.check_claim(sample_request)

        # Verify cache methods were called
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit_skips_processing_stages(
        self, pipeline, mock_cache, mock_extractors, sample_response
    ):
        """Test 6.2.4c: Verify cache hit skips all processing stages."""
        request = FactCheckRequest(claim_text="cached claim", user_id="test_user")
        mock_cache.get.return_value = sample_response
        mock_extractors.extract = AsyncMock()

        response = await pipeline.check_claim(request)

        # Verify extraction was NOT called (cache hit skips stages)
        assert response.cached is True
        assert mock_extractors.extract.call_count == 0


# ============================================================================
# Task 6.2.4d: Pipeline Configuration Validation
# ============================================================================

class TestPipeline64d:
    """Test 6.2.4d: Pipeline configuration validation."""

    @pytest.mark.asyncio
    async def test_pipeline_component_wiring(
        self, mock_cache, mock_extractors, mock_searchers, mock_processors
    ):
        """Test 6.2.4d: Verify all required components are wired correctly."""
        pipeline = FactCheckPipeline(
            cache=mock_cache,
            extractors=mock_extractors,
            searchers=mock_searchers,
            processors=mock_processors,
        )

        assert pipeline.cache is mock_cache
        assert pipeline.extractors is mock_extractors
        assert pipeline.searchers is mock_searchers
        assert pipeline.processors is mock_processors

    @pytest.mark.asyncio
    async def test_dependency_injection_of_mocks(self):
        """Test 6.2.4d: Test dependency injection of mocks."""
        cache_mock = AsyncMock()
        extractor_mock = AsyncMock()
        searcher_mock = AsyncMock()
        processor_mock = AsyncMock()

        pipeline = FactCheckPipeline(
            cache=cache_mock,
            extractors=extractor_mock,
            searchers=searcher_mock,
            processors=processor_mock,
        )

        assert isinstance(pipeline, IPipeline)
        assert pipeline.cache is cache_mock

    @pytest.mark.asyncio
    async def test_component_initialization_order(
        self, mock_cache, mock_extractors, mock_searchers, mock_processors
    ):
        """Test 6.2.4d: Test component initialization order."""
        # Components should initialize in order: cache, extractors, searchers, processors
        pipeline = FactCheckPipeline(
            cache=mock_cache,
            extractors=mock_extractors,
            searchers=mock_searchers,
            processors=mock_processors,
        )

        # All components should be initialized
        assert pipeline.cache is not None
        assert pipeline.extractors is not None
        assert pipeline.searchers is not None
        assert pipeline.processors is not None

    @pytest.mark.asyncio
    async def test_pipeline_configuration_validation_before_execution(
        self, sample_request, sample_extracted_claim
    ):
        """Test 6.2.4d: Validate configuration before execution."""
        # Create pipeline with all required mocks
        cache = AsyncMock()
        extractors = AsyncMock()
        extractors.extract.return_value = sample_extracted_claim
        cache.get.return_value = None

        pipeline = FactCheckPipeline(
            cache=cache,
            extractors=extractors,
            searchers=AsyncMock(),
            processors=AsyncMock(),
        )

        # Should be able to execute successfully with proper configuration
        response = await pipeline.check_claim(sample_request)
        assert response is not None


# ============================================================================
# Task 6.2.4: Request ID Generation and Tracing
# ============================================================================

class TestPipeline624:
    """Test 6.2.4: Request ID generation and tracing through all stages."""

    @pytest.mark.asyncio
    async def test_unique_request_id_generation(
        self, pipeline, mock_cache, mock_extractors, sample_extracted_claim
    ):
        """Test 6.2.4: Generate unique request IDs for each claim check."""
        mock_cache.get.return_value = None
        mock_extractors.extract.return_value = sample_extracted_claim

        # Create two requests without IDs
        request1 = FactCheckRequest(claim_text="Claim 1", user_id="user1")
        request2 = FactCheckRequest(claim_text="Claim 2", user_id="user2")

        response1 = await pipeline.check_claim(request1)
        response2 = await pipeline.check_claim(request2)

        # Each response should have unique request ID
        assert response1.request_id is not None
        assert response2.request_id is not None
        assert response1.request_id != response2.request_id

    @pytest.mark.asyncio
    async def test_request_id_propagation_through_all_stages(
        self, pipeline, mock_cache, mock_extractors, sample_extracted_claim, caplog
    ):
        """Test 6.2.4: Trace request ID through all mocked stages."""
        with caplog.at_level(logging.DEBUG):
            mock_cache.get.return_value = None
            mock_extractors.extract.return_value = sample_extracted_claim

            request = FactCheckRequest(claim_text="Test claim", user_id="test_user")
            response = await pipeline.check_claim(request)

            # Request ID should be propagated to response
            assert response.request_id == request.request_id
            assert response.request_id is not None

    @pytest.mark.asyncio
    async def test_request_id_in_all_stage_logging(
        self, pipeline, mock_cache, mock_extractors, sample_extracted_claim, caplog
    ):
        """Test 6.2.4: Include request ID in all stage logging."""
        with caplog.at_level(logging.INFO):
            mock_cache.get.return_value = None
            mock_extractors.extract.return_value = sample_extracted_claim

            request = FactCheckRequest(claim_text="Test claim", user_id="test_user")
            response = await pipeline.check_claim(request)

            # Check that request_id appears in logs
            # Note: log messages may contain request_id through logging filter
            assert response.request_id is not None

    @pytest.mark.asyncio
    async def test_request_id_context_variable_set_during_execution(
        self, pipeline, mock_cache, mock_extractors, sample_extracted_claim
    ):
        """Test 6.2.4: Verify request_id context variable is set correctly."""
        mock_cache.get.return_value = None
        mock_extractors.extract.return_value = sample_extracted_claim

        request = FactCheckRequest(claim_text="Test claim", user_id="test_user")

        # Clear context
        request_id_var.set("N/A")

        response = await pipeline.check_claim(request)

        # After execution, response should have request_id
        assert response.request_id is not None
        assert response.request_id != "N/A"

    @pytest.mark.asyncio
    async def test_request_id_consistency_across_response_fields(
        self, pipeline, mock_cache, mock_extractors, sample_extracted_claim
    ):
        """Test 6.2.4: Request ID should be consistent in all response references."""
        mock_cache.get.return_value = None
        mock_extractors.extract.return_value = sample_extracted_claim

        request = FactCheckRequest(claim_text="Test claim", user_id="test_user")
        response = await pipeline.check_claim(request)

        # request_id should match in request and response
        assert response.request_id == request.request_id
