"""Component-level tests for FactCheckPipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from factchecker.pipeline.factcheck_pipeline import FactCheckPipeline
from factchecker.core.models import (
    FactCheckRequest,
    FactCheckResponse,
    VerdictEnum,
)
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


# TODO: Add more comprehensive pipeline tests as implementation progresses
