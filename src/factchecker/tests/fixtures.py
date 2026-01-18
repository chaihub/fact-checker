"""Shared fixtures for component tests."""

import pytest
from datetime import datetime
from factchecker.core.models import (
    FactCheckRequest,
    ExtractedClaim,
    ClaimQuestion,
    SearchResult,
    FactCheckResponse,
    VerdictEnum,
)


@pytest.fixture
def sample_request():
    """Sample FactCheckRequest for testing."""
    return FactCheckRequest(
        claim_text="The sky is blue",
        image_data=None,
        user_id="test_user_123",
        source_platform="whatsapp",
    )


@pytest.fixture
def sample_request_with_image():
    """Sample FactCheckRequest with image."""
    return FactCheckRequest(
        claim_text=None,
        image_data=b"fake_image_data",
        user_id="test_user_456",
        source_platform="twitter",
    )


@pytest.fixture
def sample_extracted_claim():
    """Sample ExtractedClaim for testing."""
    return ExtractedClaim(
        claim_text="The sky is blue",
        extracted_from="text",
        confidence=1.0,
        raw_input_type="text_only",
        metadata={"text_length": 16},
    )


@pytest.fixture
def sample_search_results():
    """Sample SearchResult list for testing."""
    return [
        SearchResult(
            platform="twitter",
            content="The sky appears blue due to Rayleigh scattering",
            author="ScienceBot",
            url="https://twitter.com/sciencebot/123",
            timestamp=datetime.now(),
            engagement={"likes": 100, "retweets": 50},
        ),
        SearchResult(
            platform="twitter",
            content="Blue sky observations depend on weather conditions",
            author="WeatherBot",
            url="https://twitter.com/weatherbot/456",
            timestamp=datetime.now(),
            engagement={"likes": 75, "retweets": 30},
        ),
    ]


@pytest.fixture
def sample_response():
    """Sample FactCheckResponse for testing."""
    return FactCheckResponse(
        request_id="req-123",
        claim_id="claim-123",
        verdict=VerdictEnum.AUTHENTIC,
        confidence=0.95,
        evidence=[],
        references=[],
        explanation="The claim is supported by meteorological evidence.",
        search_queries_used=["sky blue", "Rayleigh scattering"],
        cached=False,
        processing_time_ms=250.5,
        timestamp=datetime.now(),
    )


@pytest.fixture
def sample_request_2():
    """FactCheckRequest for claim verification testing."""
    return FactCheckRequest(
        claim_text = (
            "The Indian Express tweets that the Pune Municipal Corporation (PMC) has initiated "
            "Artificial Intelligence (AI) skill development training for its senior officials "
            "next week. It will be held at SP College."
        ),
        image_data=None,
        user_id="verify_user_789",
        source_platform="twitter",
    )


@pytest.fixture
def sample_extracted_claim_2():
    """ExtractedClaim with questions for claim verification testing."""
    return ExtractedClaim(
        claim_text = (
            "The Indian Express tweets that the Pune Municipal Corporation (PMC) has initiated "
            "Artificial Intelligence (AI) skill development training for its senior officials "
            "next week. It will be held at SP College."
        ),
        extracted_from="text",
        confidence=0.9,
        raw_input_type="text_only",
        metadata={"text_length": 205},
        questions=[
            ClaimQuestion(
                question_type="who",
                answer_text="The Pune Municipal Corporation (PMC)",
                confidence=0.95,
            ),
            ClaimQuestion(
                question_type="what",
                answer_text="initiated Artificial Intelligence (AI) skill development training for its senior officials",
                confidence=0.9,
            ),
            ClaimQuestion(
                question_type="where",
                answer_text="SP College",
                confidence=0.8,
            ),
            ClaimQuestion(
                question_type="when",
                answer_text="next week",
                confidence=0.8,
            ),
            ClaimQuestion(
                question_type="platform",
                answer_text="twitter",
                confidence=0.9,
            )
        ]
    )
