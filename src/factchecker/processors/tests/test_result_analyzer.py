"""Tests for ResultAnalyzer."""

import pytest
from datetime import datetime
from factchecker.processors.result_analyzer import ResultAnalyzer
from factchecker.core.models import ExtractedClaim, SearchResult, VerdictEnum


@pytest.fixture
def analyzer():
    return ResultAnalyzer()


@pytest.fixture
def sample_claim():
    return ExtractedClaim(
        claim_text="The sky is blue",
        extracted_from="text",
        confidence=1.0,
        raw_input_type="text_only",
    )


@pytest.fixture
def sample_results():
    return [
        SearchResult(
            platform="twitter",
            content="The sky is blue on clear days",
            author="WeatherBot",
            url="https://twitter.com/weatherbot/123",
            timestamp=datetime.now(),
        )
    ]


@pytest.mark.asyncio
async def test_analysis_with_results(analyzer, sample_claim, sample_results):
    """Test analysis with search results."""
    verdict, confidence, explanation = await analyzer.analyze(
        sample_claim, sample_results
    )
    assert isinstance(verdict, VerdictEnum)
    assert 0 <= confidence <= 1
    assert isinstance(explanation, str)


@pytest.mark.asyncio
async def test_analysis_without_results(analyzer, sample_claim):
    """Test analysis with no results."""
    verdict, confidence, explanation = await analyzer.analyze(sample_claim, [])
    assert verdict == VerdictEnum.UNCLEAR
    assert isinstance(confidence, float)
    assert isinstance(explanation, str)
