"""Tests for ResponseGenerator."""

import pytest
from datetime import datetime
from factchecker.processors.response_generator import ResponseGenerator
from factchecker.core.models import ExtractedClaim, SearchResult, VerdictEnum


@pytest.fixture
def generator():
    return ResponseGenerator()


@pytest.fixture
def sample_claim():
    return ExtractedClaim(
        claim_text="Test claim",
        extracted_from="text",
        confidence=1.0,
        raw_input_type="text_only",
    )


@pytest.fixture
def sample_results():
    return [
        SearchResult(
            platform="twitter",
            content="Sample result",
            author="TestUser",
            url="https://twitter.com/test/123",
            timestamp=datetime.now(),
        )
    ]


@pytest.mark.asyncio
async def test_response_generation(generator, sample_claim, sample_results):
    """Test response generation."""
    response = await generator.generate(
        claim=sample_claim,
        results=sample_results,
        verdict=VerdictEnum.AUTHENTIC,
        confidence=0.9,
        explanation="Test explanation",
    )
    assert isinstance(response, dict)
    assert "verdict" in response
    assert "confidence" in response
    assert "evidence" in response
    assert "references" in response
    assert "explanation" in response
    assert response["verdict"] == VerdictEnum.AUTHENTIC
    assert response["confidence"] == 0.9
