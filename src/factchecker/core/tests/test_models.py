"""Tests for all data models in core.models module."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from factchecker.core.models import (
    FactCheckRequest,
    ExtractedClaim,
    ClaimQuestion,
    SearchResult,
    VerdictEnum,
    Reference,
    Evidence,
    FactCheckResponse,
)


# ============================================================================
# FactCheckRequest Tests (14 tests)
# ============================================================================

class TestFactCheckRequest:
    """Tests for FactCheckRequest model."""

    def test_factcheck_request_missing_user_id(self):
        """Test that user_id is required."""
        with pytest.raises(ValidationError, match="user_id"):
            FactCheckRequest(claim_text="test")

    def test_factcheck_request_default_source_platform(self):
        """Test that source_platform defaults to 'whatsapp'."""
        request = FactCheckRequest(
            claim_text="test",
            user_id="user1",
        )
        assert request.source_platform == "whatsapp"

    def test_factcheck_request_custom_source_platform(self):
        """Test that source_platform can be overridden."""
        request = FactCheckRequest(
            claim_text="test",
            user_id="user1",
            source_platform="twitter",
        )
        assert request.source_platform == "twitter"

    def test_factcheck_request_claim_text_only(self):
        """Test request with claim_text only is valid."""
        request = FactCheckRequest(
            claim_text="The sky is blue",
            user_id="user1",
        )
        assert request.claim_text == "The sky is blue"
        assert request.image_data is None

    def test_factcheck_request_image_data_only(self):
        """Test request with image_data only is valid."""
        request = FactCheckRequest(
            image_data=b"fake_image_data",
            user_id="user1",
        )
        assert request.image_data == b"fake_image_data"
        assert request.claim_text is None

    def test_factcheck_request_both_provided(self):
        """Test request with both claim_text and image_data is valid."""
        request = FactCheckRequest(
            claim_text="test text",
            image_data=b"fake_image_data",
            user_id="user1",
        )
        assert request.claim_text == "test text"
        assert request.image_data == b"fake_image_data"

    def test_factcheck_request_neither_provided(self):
        """Test that at least one of claim_text or image_data is required."""
        with pytest.raises(ValidationError, match="At least one"):
            FactCheckRequest(user_id="user1")

    def test_factcheck_request_empty_text_fails(self):
        """Test that empty string for claim_text fails validation."""
        with pytest.raises(ValidationError, match="At least one"):
            FactCheckRequest(
                claim_text="",
                image_data=None,
                user_id="user1",
            )

    def test_factcheck_request_empty_bytes_fails(self):
        """Test that empty bytes for image_data fails validation."""
        with pytest.raises(ValidationError, match="At least one"):
            FactCheckRequest(
                claim_text=None,
                image_data=b"",
                user_id="user1",
            )

    def test_factcheck_request_whitespace_stripping(self):
        """Test that claim_text whitespace is stripped."""
        request = FactCheckRequest(
            claim_text="  test claim  ",
            user_id="user1",
        )
        assert request.claim_text == "test claim"

    def test_factcheck_request_optional_request_id(self):
        """Test that request_id is optional."""
        request = FactCheckRequest(
            claim_text="test",
            user_id="user1",
        )
        assert request.request_id is None

    def test_factcheck_request_custom_request_id(self):
        """Test that request_id can be provided."""
        request = FactCheckRequest(
            claim_text="test",
            user_id="user1",
            request_id="custom-id-123",
        )
        assert request.request_id == "custom-id-123"

    def test_factcheck_request_whitespace_only_claim_text(self):
        """Test that whitespace-only claim_text fails validation."""
        with pytest.raises(ValidationError, match="At least one"):
            FactCheckRequest(
                claim_text="   ",
                user_id="user1",
            )

    def test_factcheck_request_image_data_with_claim_text_whitespace(self):
        """Test that image_data only is valid even with whitespace claim_text."""
        request = FactCheckRequest(
            claim_text="   ",
            image_data=b"data",
            user_id="user1",
        )
        assert request.image_data == b"data"


# ============================================================================
# ExtractedClaim Tests (12 tests)
# ============================================================================

class TestExtractedClaim:
    """Tests for ExtractedClaim model."""

    def test_extracted_claim_missing_claim_text(self):
        """Test that claim_text is required."""
        with pytest.raises(ValidationError, match="claim_text"):
            ExtractedClaim(
                extracted_from="text",
                confidence=0.95,
                raw_input_type="text_only",
            )

    def test_extracted_claim_missing_extracted_from(self):
        """Test that extracted_from is required."""
        with pytest.raises(ValidationError, match="extracted_from"):
            ExtractedClaim(
                claim_text="test",
                confidence=0.95,
                raw_input_type="text_only",
            )

    def test_extracted_claim_missing_confidence(self):
        """Test that confidence is required."""
        with pytest.raises(ValidationError, match="confidence"):
            ExtractedClaim(
                claim_text="test",
                extracted_from="text",
                raw_input_type="text_only",
            )

    def test_extracted_claim_missing_raw_input_type(self):
        """Test that raw_input_type is required."""
        with pytest.raises(ValidationError, match="raw_input_type"):
            ExtractedClaim(
                claim_text="test",
                extracted_from="text",
                confidence=0.95,
            )

    def test_extracted_claim_valid_extracted_from_text(self):
        """Test that 'text' is valid for extracted_from."""
        claim = ExtractedClaim(
            claim_text="test",
            extracted_from="text",
            confidence=0.95,
            raw_input_type="text_only",
        )
        assert claim.extracted_from == "text"

    def test_extracted_claim_valid_extracted_from_image(self):
        """Test that 'image' is valid for extracted_from."""
        claim = ExtractedClaim(
            claim_text="test",
            extracted_from="image",
            confidence=0.95,
            raw_input_type="image_only",
        )
        assert claim.extracted_from == "image"

    def test_extracted_claim_valid_extracted_from_hybrid(self):
        """Test that 'hybrid' is valid for extracted_from."""
        claim = ExtractedClaim(
            claim_text="test",
            extracted_from="hybrid",
            confidence=0.95,
            raw_input_type="both",
        )
        assert claim.extracted_from == "hybrid"

    def test_extracted_claim_invalid_extracted_from(self):
        """Test that invalid extracted_from value is rejected."""
        with pytest.raises(ValidationError, match="extracted_from"):
            ExtractedClaim(
                claim_text="test",
                extracted_from="invalid_value",
                confidence=0.95,
                raw_input_type="text_only",
            )

    def test_extracted_claim_valid_raw_input_type_values(self):
        """Test all valid raw_input_type values."""
        for raw_type in ["text_only", "image_only", "both"]:
            claim = ExtractedClaim(
                claim_text="test",
                extracted_from="text",
                confidence=0.95,
                raw_input_type=raw_type,
            )
            assert claim.raw_input_type == raw_type

    def test_extracted_claim_invalid_raw_input_type(self):
        """Test that invalid raw_input_type value is rejected."""
        with pytest.raises(ValidationError, match="raw_input_type"):
            ExtractedClaim(
                claim_text="test",
                extracted_from="text",
                confidence=0.95,
                raw_input_type="invalid_type",
            )

    def test_extracted_claim_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        claim = ExtractedClaim(
            claim_text="test",
            extracted_from="text",
            confidence=0.95,
            raw_input_type="text_only",
        )
        assert claim.metadata == {}

    def test_extracted_claim_custom_metadata(self):
        """Test that custom metadata can be provided."""
        metadata = {"text_length": 20, "language": "en"}
        claim = ExtractedClaim(
            claim_text="test",
            extracted_from="text",
            confidence=0.95,
            raw_input_type="text_only",
            metadata=metadata,
        )
        assert claim.metadata == metadata

    def test_extracted_claim_default_questions(self):
        """Test that questions defaults to empty list."""
        claim = ExtractedClaim(
            claim_text="test",
            extracted_from="text",
            confidence=0.95,
            raw_input_type="text_only",
        )
        assert claim.questions == []

    def test_extracted_claim_with_questions(self):
        """Test that ExtractedClaim can have questions."""
        question = ClaimQuestion(
            question_type="who",
            question_text="Who made this claim?",
            confidence=0.85,
        )
        claim = ExtractedClaim(
            claim_text="test",
            extracted_from="text",
            confidence=0.95,
            raw_input_type="text_only",
            questions=[question],
        )
        assert len(claim.questions) == 1
        assert isinstance(claim.questions[0], ClaimQuestion)
        assert claim.questions[0].question_type == "who"

    def test_extracted_claim_with_multiple_questions(self):
        """Test that ExtractedClaim can have multiple questions."""
        questions = [
            ClaimQuestion(
                question_type="who",
                question_text="Who made this claim?",
                confidence=0.85,
            ),
            ClaimQuestion(
                question_type="when",
                question_text="When did this happen?",
                related_entity="event",
                confidence=0.75,
            ),
        ]
        claim = ExtractedClaim(
            claim_text="test",
            extracted_from="text",
            confidence=0.95,
            raw_input_type="text_only",
            questions=questions,
        )
        assert len(claim.questions) == 2
        assert claim.questions[0].question_type == "who"
        assert claim.questions[1].question_type == "when"


# ============================================================================
# ClaimQuestion Tests (10 tests)
# ============================================================================

class TestClaimQuestion:
    """Tests for ClaimQuestion model."""

    def test_claim_question_missing_question_type(self):
        """Test that question_type is required."""
        with pytest.raises(ValidationError, match="question_type"):
            ClaimQuestion(
                question_text="Who made this claim?",
                confidence=0.85,
            )

    def test_claim_question_missing_question_text(self):
        """Test that question_text is required."""
        with pytest.raises(ValidationError, match="question_text"):
            ClaimQuestion(
                question_type="who",
                confidence=0.85,
            )

    def test_claim_question_missing_confidence(self):
        """Test that confidence is required."""
        with pytest.raises(ValidationError, match="confidence"):
            ClaimQuestion(
                question_type="who",
                question_text="Who made this claim?",
            )

    def test_claim_question_valid_question_types(self):
        """Test all valid question_type values."""
        for q_type in ["who", "when", "where", "what", "how", "why"]:
            question = ClaimQuestion(
                question_type=q_type,
                question_text=f"Test {q_type} question",
                confidence=0.85,
            )
            assert question.question_type == q_type

    def test_claim_question_invalid_question_type(self):
        """Test that invalid question_type value is rejected."""
        with pytest.raises(ValidationError, match="question_type"):
            ClaimQuestion(
                question_type="invalid_type",
                question_text="Test question",
                confidence=0.85,
            )

    def test_claim_question_optional_related_entity(self):
        """Test that related_entity is optional."""
        question = ClaimQuestion(
            question_type="who",
            question_text="Who made this claim?",
            confidence=0.85,
        )
        assert question.related_entity is None

    def test_claim_question_with_related_entity(self):
        """Test that related_entity can be provided."""
        question = ClaimQuestion(
            question_type="who",
            question_text="Who made this claim?",
            related_entity="John Doe",
            confidence=0.85,
        )
        assert question.related_entity == "John Doe"

    def test_claim_question_confidence_boundary_values(self):
        """Test boundary values for confidence."""
        for conf_value in [0.0, 0.5, 1.0]:
            question = ClaimQuestion(
                question_type="who",
                question_text="Who made this claim?",
                confidence=conf_value,
            )
            assert question.confidence == conf_value

    def test_claim_question_empty_question_text_fails(self):
        """Test that empty question_text fails validation."""
        with pytest.raises(ValidationError):
            ClaimQuestion(
                question_type="who",
                question_text="",
                confidence=0.85,
            )

    def test_claim_question_full_creation(self):
        """Test successful creation of complete ClaimQuestion."""
        question = ClaimQuestion(
            question_type="when",
            question_text="When did this event occur?",
            related_entity="event",
            confidence=0.92,
        )
        assert question.question_type == "when"
        assert question.question_text == "When did this event occur?"
        assert question.related_entity == "event"
        assert question.confidence == 0.92


# ============================================================================
# SearchResult Tests (10 tests)
# ============================================================================

class TestSearchResult:
    """Tests for SearchResult model."""

    def test_search_result_missing_platform(self):
        """Test that platform is required."""
        with pytest.raises(ValidationError, match="platform"):
            SearchResult(
                content="test",
                author="user",
                url="https://twitter.com/user/123",
                timestamp=datetime.now(),
            )

    def test_search_result_missing_content(self):
        """Test that content is required."""
        with pytest.raises(ValidationError, match="content"):
            SearchResult(
                platform="twitter",
                author="user",
                url="https://twitter.com/user/123",
                timestamp=datetime.now(),
            )

    def test_search_result_missing_author(self):
        """Test that author is required."""
        with pytest.raises(ValidationError, match="author"):
            SearchResult(
                platform="twitter",
                content="test",
                url="https://twitter.com/user/123",
                timestamp=datetime.now(),
            )

    def test_search_result_missing_url(self):
        """Test that url is required."""
        with pytest.raises(ValidationError, match="url"):
            SearchResult(
                platform="twitter",
                content="test",
                author="user",
                timestamp=datetime.now(),
            )

    def test_search_result_missing_timestamp(self):
        """Test that timestamp is required."""
        with pytest.raises(ValidationError, match="timestamp"):
            SearchResult(
                platform="twitter",
                content="test",
                author="user",
                url="https://twitter.com/user/123",
            )

    def test_search_result_timestamp_from_iso_string(self):
        """Test that ISO string is converted to datetime."""
        result = SearchResult(
            platform="twitter",
            content="test",
            author="user",
            url="https://twitter.com/user/123",
            timestamp="2025-11-29T10:30:00",
        )
        assert isinstance(result.timestamp, datetime)

    def test_search_result_timestamp_from_datetime_object(self):
        """Test that datetime object is accepted as-is."""
        now = datetime.now()
        result = SearchResult(
            platform="twitter",
            content="test",
            author="user",
            url="https://twitter.com/user/123",
            timestamp=now,
        )
        assert result.timestamp == now

    def test_search_result_default_engagement(self):
        """Test that engagement defaults to empty dict."""
        result = SearchResult(
            platform="twitter",
            content="test",
            author="user",
            url="https://twitter.com/user/123",
            timestamp=datetime.now(),
        )
        assert result.engagement == {}

    def test_search_result_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        result = SearchResult(
            platform="twitter",
            content="test",
            author="user",
            url="https://twitter.com/user/123",
            timestamp=datetime.now(),
        )
        assert result.metadata == {}

    def test_search_result_custom_engagement_and_metadata(self):
        """Test that custom engagement and metadata can be provided."""
        engagement = {"likes": 100, "retweets": 50}
        metadata = {"source": "official"}
        result = SearchResult(
            platform="twitter",
            content="test",
            author="user",
            url="https://twitter.com/user/123",
            timestamp=datetime.now(),
            engagement=engagement,
            metadata=metadata,
        )
        assert result.engagement == engagement
        assert result.metadata == metadata


# ============================================================================
# VerdictEnum Tests (5 tests)
# ============================================================================

class TestVerdictEnum:
    """Tests for VerdictEnum enum."""

    def test_verdict_enum_authentic_value(self):
        """Test AUTHENTIC enum value."""
        assert VerdictEnum.AUTHENTIC == "authentic"

    def test_verdict_enum_not_authentic_value(self):
        """Test NOT_AUTHENTIC enum value."""
        assert VerdictEnum.NOT_AUTHENTIC == "not_authentic"

    def test_verdict_enum_mixed_value(self):
        """Test MIXED enum value."""
        assert VerdictEnum.MIXED == "mixed"

    def test_verdict_enum_unclear_value(self):
        """Test UNCLEAR enum value."""
        assert VerdictEnum.UNCLEAR == "unclear"

    def test_verdict_enum_invalid_value(self):
        """Test that invalid enum value is rejected."""
        with pytest.raises(ValueError):
            VerdictEnum("invalid_value")


# ============================================================================
# Reference Tests (5 tests)
# ============================================================================

class TestReference:
    """Tests for Reference model."""

    def test_reference_missing_title(self):
        """Test that title is required."""
        with pytest.raises(ValidationError, match="title"):
            Reference(
                url="https://example.com",
                snippet="test snippet",
                platform="twitter",
            )

    def test_reference_missing_url(self):
        """Test that url is required."""
        with pytest.raises(ValidationError, match="url"):
            Reference(
                title="Test Article",
                snippet="test snippet",
                platform="twitter",
            )

    def test_reference_missing_snippet(self):
        """Test that snippet is required."""
        with pytest.raises(ValidationError, match="snippet"):
            Reference(
                title="Test Article",
                url="https://example.com",
                platform="twitter",
            )

    def test_reference_missing_platform(self):
        """Test that platform is required."""
        with pytest.raises(ValidationError, match="platform"):
            Reference(
                title="Test Article",
                url="https://example.com",
                snippet="test snippet",
            )

    def test_reference_creation_success(self):
        """Test successful creation of Reference."""
        ref = Reference(
            title="Test Article",
            url="https://example.com",
            snippet="test snippet",
            platform="twitter",
        )
        assert ref.title == "Test Article"
        assert ref.url == "https://example.com"
        assert ref.snippet == "test snippet"
        assert ref.platform == "twitter"


# ============================================================================
# Evidence Tests (11 tests)
# ============================================================================

class TestEvidence:
    """Tests for Evidence model with nested SearchResult validation."""

    def test_evidence_missing_claim_fragment(self):
        """Test that claim_fragment is required."""
        with pytest.raises(ValidationError, match="claim_fragment"):
            Evidence(
                finding="finding text",
                supporting_results=[],
                confidence=0.95,
            )

    def test_evidence_missing_finding(self):
        """Test that finding is required."""
        with pytest.raises(ValidationError, match="finding"):
            Evidence(
                claim_fragment="fragment",
                supporting_results=[],
                confidence=0.95,
            )

    def test_evidence_missing_supporting_results(self):
        """Test that supporting_results is required."""
        with pytest.raises(ValidationError, match="supporting_results"):
            Evidence(
                claim_fragment="fragment",
                finding="finding text",
                confidence=0.95,
            )

    def test_evidence_missing_confidence(self):
        """Test that confidence is required."""
        with pytest.raises(ValidationError, match="confidence"):
            Evidence(
                claim_fragment="fragment",
                finding="finding text",
                supporting_results=[],
            )

    def test_evidence_empty_supporting_results(self):
        """Test that empty supporting_results list is allowed."""
        evidence = Evidence(
            claim_fragment="fragment",
            finding="finding text",
            supporting_results=[],
            confidence=0.95,
        )
        assert evidence.supporting_results == []

    def test_evidence_supporting_results_single_item(self):
        """Test Evidence with single SearchResult."""
        result = SearchResult(
            platform="twitter",
            content="test",
            author="user",
            url="https://twitter.com/user/123",
            timestamp=datetime.now(),
        )
        evidence = Evidence(
            claim_fragment="fragment",
            finding="finding text",
            supporting_results=[result],
            confidence=0.95,
        )
        assert len(evidence.supporting_results) == 1
        assert evidence.supporting_results[0] == result

    def test_evidence_supporting_results_multiple_items(self):
        """Test Evidence with multiple SearchResults."""
        results = [
            SearchResult(
                platform="twitter",
                content="test1",
                author="user1",
                url="https://twitter.com/user/1",
                timestamp=datetime.now(),
            ),
            SearchResult(
                platform="bluesky",
                content="test2",
                author="user2",
                url="https://bluesky.com/user/2",
                timestamp=datetime.now(),
            ),
        ]
        evidence = Evidence(
            claim_fragment="fragment",
            finding="finding text",
            supporting_results=results,
            confidence=0.95,
        )
        assert len(evidence.supporting_results) == 2

    def test_evidence_invalid_supporting_results_missing_field(self):
        """Test that invalid SearchResult in list bubbles up validation error."""
        with pytest.raises(ValidationError):
            Evidence(
                claim_fragment="fragment",
                finding="finding text",
                confidence=0.95,
                supporting_results=[
                    {
                        # Missing required 'platform' field
                        "content": "test",
                        "author": "user",
                        "url": "https://twitter.com/user/123",
                        "timestamp": datetime.now(),
                    }
                ],
            )

    def test_evidence_supporting_results_dict_coercion(self):
        """Test that dict dicts are converted to SearchResult instances."""
        evidence = Evidence(
            claim_fragment="fragment",
            finding="finding text",
            confidence=0.95,
            supporting_results=[
                {
                    "platform": "twitter",
                    "content": "test",
                    "author": "user",
                    "url": "https://twitter.com/user/123",
                    "timestamp": datetime.now(),
                }
            ],
        )
        assert len(evidence.supporting_results) == 1
        assert isinstance(evidence.supporting_results[0], SearchResult)

    def test_evidence_confidence_boundary_values(self):
        """Test boundary values for confidence."""
        for conf_value in [0.0, 0.5, 1.0]:
            evidence = Evidence(
                claim_fragment="fragment",
                finding="finding text",
                supporting_results=[],
                confidence=conf_value,
            )
            assert evidence.confidence == conf_value


# ============================================================================
# FactCheckResponse Tests (18 tests)
# ============================================================================

class TestFactCheckResponse:
    """Tests for FactCheckResponse model with complex nested validation."""

    def test_factcheck_response_missing_request_id(self):
        """Test that request_id is required."""
        with pytest.raises(ValidationError, match="request_id"):
            FactCheckResponse(
                claim_id="claim1",
                verdict=VerdictEnum.AUTHENTIC,
                confidence=0.95,
                evidence=[],
                references=[],
                explanation="test",
                search_queries_used=[],
                cached=False,
                processing_time_ms=100.0,
                timestamp=datetime.now(),
            )

    def test_factcheck_response_missing_claim_id(self):
        """Test that claim_id is required."""
        with pytest.raises(ValidationError, match="claim_id"):
            FactCheckResponse(
                request_id="req1",
                verdict=VerdictEnum.AUTHENTIC,
                confidence=0.95,
                evidence=[],
                references=[],
                explanation="test",
                search_queries_used=[],
                cached=False,
                processing_time_ms=100.0,
                timestamp=datetime.now(),
            )

    def test_factcheck_response_missing_verdict(self):
        """Test that verdict is required."""
        with pytest.raises(ValidationError, match="verdict"):
            FactCheckResponse(
                request_id="req1",
                claim_id="claim1",
                confidence=0.95,
                evidence=[],
                references=[],
                explanation="test",
                search_queries_used=[],
                cached=False,
                processing_time_ms=100.0,
                timestamp=datetime.now(),
            )

    def test_factcheck_response_missing_confidence(self):
        """Test that confidence is required."""
        with pytest.raises(ValidationError, match="confidence"):
            FactCheckResponse(
                request_id="req1",
                claim_id="claim1",
                verdict=VerdictEnum.AUTHENTIC,
                evidence=[],
                references=[],
                explanation="test",
                search_queries_used=[],
                cached=False,
                processing_time_ms=100.0,
                timestamp=datetime.now(),
            )

    def test_factcheck_response_missing_evidence(self):
        """Test that evidence is required."""
        with pytest.raises(ValidationError, match="evidence"):
            FactCheckResponse(
                request_id="req1",
                claim_id="claim1",
                verdict=VerdictEnum.AUTHENTIC,
                confidence=0.95,
                references=[],
                explanation="test",
                search_queries_used=[],
                cached=False,
                processing_time_ms=100.0,
                timestamp=datetime.now(),
            )

    def test_factcheck_response_missing_references(self):
        """Test that references is required."""
        with pytest.raises(ValidationError, match="references"):
            FactCheckResponse(
                request_id="req1",
                claim_id="claim1",
                verdict=VerdictEnum.AUTHENTIC,
                confidence=0.95,
                evidence=[],
                explanation="test",
                search_queries_used=[],
                cached=False,
                processing_time_ms=100.0,
                timestamp=datetime.now(),
            )

    def test_factcheck_response_missing_explanation(self):
        """Test that explanation is required."""
        with pytest.raises(ValidationError, match="explanation"):
            FactCheckResponse(
                request_id="req1",
                claim_id="claim1",
                verdict=VerdictEnum.AUTHENTIC,
                confidence=0.95,
                evidence=[],
                references=[],
                search_queries_used=[],
                cached=False,
                processing_time_ms=100.0,
                timestamp=datetime.now(),
            )

    def test_factcheck_response_missing_search_queries_used(self):
        """Test that search_queries_used is required."""
        with pytest.raises(ValidationError, match="search_queries_used"):
            FactCheckResponse(
                request_id="req1",
                claim_id="claim1",
                verdict=VerdictEnum.AUTHENTIC,
                confidence=0.95,
                evidence=[],
                references=[],
                explanation="test",
                cached=False,
                processing_time_ms=100.0,
                timestamp=datetime.now(),
            )

    def test_factcheck_response_missing_cached(self):
        """Test that cached is required."""
        with pytest.raises(ValidationError, match="cached"):
            FactCheckResponse(
                request_id="req1",
                claim_id="claim1",
                verdict=VerdictEnum.AUTHENTIC,
                confidence=0.95,
                evidence=[],
                references=[],
                explanation="test",
                search_queries_used=[],
                processing_time_ms=100.0,
                timestamp=datetime.now(),
            )

    def test_factcheck_response_missing_processing_time_ms(self):
        """Test that processing_time_ms is required."""
        with pytest.raises(ValidationError, match="processing_time_ms"):
            FactCheckResponse(
                request_id="req1",
                claim_id="claim1",
                verdict=VerdictEnum.AUTHENTIC,
                confidence=0.95,
                evidence=[],
                references=[],
                explanation="test",
                search_queries_used=[],
                cached=False,
                timestamp=datetime.now(),
            )

    def test_factcheck_response_missing_timestamp(self):
        """Test that timestamp is required."""
        with pytest.raises(ValidationError, match="timestamp"):
            FactCheckResponse(
                request_id="req1",
                claim_id="claim1",
                verdict=VerdictEnum.AUTHENTIC,
                confidence=0.95,
                evidence=[],
                references=[],
                explanation="test",
                search_queries_used=[],
                cached=False,
                processing_time_ms=100.0,
            )

    def test_factcheck_response_empty_evidence(self):
        """Test that empty evidence list is allowed."""
        response = FactCheckResponse(
            request_id="req1",
            claim_id="claim1",
            verdict=VerdictEnum.AUTHENTIC,
            confidence=0.95,
            evidence=[],
            references=[],
            explanation="test",
            search_queries_used=[],
            cached=False,
            processing_time_ms=100.0,
            timestamp=datetime.now(),
        )
        assert response.evidence == []

    def test_factcheck_response_empty_references(self):
        """Test that empty references list is allowed."""
        response = FactCheckResponse(
            request_id="req1",
            claim_id="claim1",
            verdict=VerdictEnum.AUTHENTIC,
            confidence=0.95,
            evidence=[],
            references=[],
            explanation="test",
            search_queries_used=[],
            cached=False,
            processing_time_ms=100.0,
            timestamp=datetime.now(),
        )
        assert response.references == []

    def test_factcheck_response_empty_search_queries(self):
        """Test that empty search_queries_used list is allowed."""
        response = FactCheckResponse(
            request_id="req1",
            claim_id="claim1",
            verdict=VerdictEnum.AUTHENTIC,
            confidence=0.95,
            evidence=[],
            references=[],
            explanation="test",
            search_queries_used=[],
            cached=False,
            processing_time_ms=100.0,
            timestamp=datetime.now(),
        )
        assert response.search_queries_used == []

    def test_factcheck_response_valid_evidence_list(self):
        """Test FactCheckResponse with valid Evidence list."""
        evidence = Evidence(
            claim_fragment="fragment",
            finding="finding text",
            supporting_results=[],
            confidence=0.95,
        )
        response = FactCheckResponse(
            request_id="req1",
            claim_id="claim1",
            verdict=VerdictEnum.AUTHENTIC,
            confidence=0.95,
            evidence=[evidence],
            references=[],
            explanation="test",
            search_queries_used=["query1"],
            cached=False,
            processing_time_ms=100.0,
            timestamp=datetime.now(),
        )
        assert len(response.evidence) == 1
        assert isinstance(response.evidence[0], Evidence)

    def test_factcheck_response_valid_references_list(self):
        """Test FactCheckResponse with valid Reference list."""
        ref = Reference(
            title="Test",
            url="https://example.com",
            snippet="snippet",
            platform="twitter",
        )
        response = FactCheckResponse(
            request_id="req1",
            claim_id="claim1",
            verdict=VerdictEnum.AUTHENTIC,
            confidence=0.95,
            evidence=[],
            references=[ref],
            explanation="test",
            search_queries_used=["query1"],
            cached=False,
            processing_time_ms=100.0,
            timestamp=datetime.now(),
        )
        assert len(response.references) == 1
        assert isinstance(response.references[0], Reference)

    def test_factcheck_response_invalid_verdict(self):
        """Test that invalid verdict value is rejected."""
        with pytest.raises(ValidationError, match="verdict"):
            FactCheckResponse(
                request_id="req1",
                claim_id="claim1",
                verdict="invalid_verdict",
                confidence=0.95,
                evidence=[],
                references=[],
                explanation="test",
                search_queries_used=[],
                cached=False,
                processing_time_ms=100.0,
                timestamp=datetime.now(),
            )

    def test_factcheck_response_full_creation(self):
        """Test successful creation of complete FactCheckResponse."""
        response = FactCheckResponse(
            request_id="req123",
            claim_id="claim456",
            verdict=VerdictEnum.AUTHENTIC,
            confidence=0.92,
            evidence=[],
            references=[],
            explanation="The claim is supported by evidence.",
            search_queries_used=["query1", "query2"],
            cached=False,
            processing_time_ms=234.5,
            timestamp=datetime.now(),
        )
        assert response.request_id == "req123"
        assert response.claim_id == "claim456"
        assert response.verdict == VerdictEnum.AUTHENTIC
        assert response.confidence == 0.92
