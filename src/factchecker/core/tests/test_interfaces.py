"""Tests for abstract interfaces and their implementations."""

import pytest
import inspect
from typing import List, Optional
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from factchecker.core.interfaces import (
    BaseExtractor,
    BaseSearcher,
    BaseProcessor,
    IPipeline,
)
from factchecker.core.models import (
    ExtractedClaim,
    SearchResult,
    FactCheckRequest,
    FactCheckResponse,
)
from factchecker.extractors.text_extractor import TextExtractor
from factchecker.extractors.image_extractor import ImageExtractor
from factchecker.searchers.twitter_searcher import TwitterSearcher
from factchecker.searchers.bluesky_searcher import BlueSkySearcher
from factchecker.processors.result_analyzer import ResultAnalyzer
from factchecker.processors.response_generator import ResponseGenerator


# ============================================================================
# Abstract Class Instantiation Tests (5 tests)
# ============================================================================


class TestAbstractClassInstantiation:
    """Test that abstract classes cannot be instantiated."""

    def test_base_extractor_cannot_be_instantiated(self):
        """Test that BaseExtractor is abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="abstract"):
            BaseExtractor()

    def test_base_searcher_cannot_be_instantiated(self):
        """Test that BaseSearcher is abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="abstract"):
            BaseSearcher()

    def test_base_processor_cannot_be_instantiated(self):
        """Test that BaseProcessor is abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="abstract"):
            BaseProcessor()

    def test_ipipeline_cannot_be_instantiated(self):
        """Test that IPipeline is abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="abstract"):
            IPipeline()

    def test_abstract_base_class_is_abc(self):
        """Test that interfaces are proper ABC subclasses."""
        from abc import ABC

        assert issubclass(BaseExtractor, ABC)
        assert issubclass(BaseSearcher, ABC)
        assert issubclass(BaseProcessor, ABC)
        assert issubclass(IPipeline, ABC)


# ============================================================================
# Abstract Method Definition Tests (8 tests)
# ============================================================================


class TestAbstractMethodDefinitions:
    """Test that abstract methods are properly defined."""

    def test_base_extractor_has_extract_method(self):
        """Test that BaseExtractor defines extract method."""
        assert hasattr(BaseExtractor, "extract")
        assert callable(getattr(BaseExtractor, "extract"))

    def test_base_extractor_extract_is_abstract(self):
        """Test that extract is marked as abstract."""
        method = getattr(BaseExtractor, "extract")
        assert hasattr(method, "__isabstractmethod__")
        assert method.__isabstractmethod__ is True

    def test_base_searcher_has_search_method(self):
        """Test that BaseSearcher defines search method."""
        assert hasattr(BaseSearcher, "search")
        assert callable(getattr(BaseSearcher, "search"))

    def test_base_searcher_search_is_abstract(self):
        """Test that search is marked as abstract."""
        method = getattr(BaseSearcher, "search")
        assert hasattr(method, "__isabstractmethod__")
        assert method.__isabstractmethod__ is True

    def test_base_searcher_has_platform_name_property(self):
        """Test that BaseSearcher defines platform_name property."""
        assert hasattr(BaseSearcher, "platform_name")

    def test_base_searcher_platform_name_is_abstract(self):
        """Test that platform_name is marked as abstract."""
        prop = getattr(BaseSearcher, "platform_name")
        assert hasattr(prop.fget, "__isabstractmethod__")
        assert prop.fget.__isabstractmethod__ is True

    def test_base_processor_has_process_method(self):
        """Test that BaseProcessor defines process method."""
        assert hasattr(BaseProcessor, "process")
        assert callable(getattr(BaseProcessor, "process"))

    def test_ipipeline_has_check_claim_method(self):
        """Test that IPipeline defines check_claim method."""
        assert hasattr(IPipeline, "check_claim")
        assert callable(getattr(IPipeline, "check_claim"))


# ============================================================================
# TextExtractor Compliance Tests (4 tests)
# ============================================================================


class TestTextExtractorCompliance:
    """Test that TextExtractor properly implements BaseExtractor."""

    def test_text_extractor_is_base_extractor(self):
        """Test that TextExtractor is a BaseExtractor."""
        assert issubclass(TextExtractor, BaseExtractor)

    def test_text_extractor_can_be_instantiated(self):
        """Test that TextExtractor can be instantiated."""
        extractor = TextExtractor()
        assert isinstance(extractor, BaseExtractor)

    @pytest.mark.asyncio
    async def test_text_extractor_extract_method_exists(self):
        """Test that TextExtractor implements extract method."""
        extractor = TextExtractor()
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)

    @pytest.mark.asyncio
    async def test_text_extractor_extract_returns_extracted_claim(self):
        """Test that extract returns ExtractedClaim."""
        extractor = TextExtractor()
        result = await extractor.extract("test claim", None)
        assert isinstance(result, ExtractedClaim)


# ============================================================================
# ImageExtractor Compliance Tests (4 tests)
# ============================================================================


class TestImageExtractorCompliance:
    """Test that ImageExtractor properly implements BaseExtractor."""

    def test_image_extractor_is_base_extractor(self):
        """Test that ImageExtractor is a BaseExtractor."""
        assert issubclass(ImageExtractor, BaseExtractor)

    def test_image_extractor_can_be_instantiated(self):
        """Test that ImageExtractor can be instantiated."""
        extractor = ImageExtractor()
        assert isinstance(extractor, BaseExtractor)

    @pytest.mark.asyncio
    async def test_image_extractor_extract_method_exists(self):
        """Test that ImageExtractor implements extract method."""
        extractor = ImageExtractor()
        assert hasattr(extractor, "extract")
        assert callable(extractor.extract)

    @pytest.mark.asyncio
    async def test_image_extractor_extract_returns_extracted_claim(self):
        """Test that extract returns ExtractedClaim."""
        extractor = ImageExtractor()
        result = await extractor.extract(None, b"fake_image_data")
        assert isinstance(result, ExtractedClaim)


# ============================================================================
# TwitterSearcher Compliance Tests (5 tests)
# ============================================================================


class TestTwitterSearcherCompliance:
    """Test that TwitterSearcher properly implements BaseSearcher."""

    def test_twitter_searcher_is_base_searcher(self):
        """Test that TwitterSearcher is a BaseSearcher."""
        assert issubclass(TwitterSearcher, BaseSearcher)

    def test_twitter_searcher_can_be_instantiated(self):
        """Test that TwitterSearcher can be instantiated."""
        searcher = TwitterSearcher()
        assert isinstance(searcher, BaseSearcher)

    def test_twitter_searcher_has_platform_name_property(self):
        """Test that TwitterSearcher has platform_name property."""
        searcher = TwitterSearcher()
        assert hasattr(searcher, "platform_name")

    def test_twitter_searcher_platform_name_returns_string(self):
        """Test that platform_name returns a string."""
        searcher = TwitterSearcher()
        assert isinstance(searcher.platform_name, str)
        assert searcher.platform_name == "twitter"

    @pytest.mark.asyncio
    async def test_twitter_searcher_search_method_exists(self):
        """Test that TwitterSearcher implements search method."""
        searcher = TwitterSearcher()
        assert hasattr(searcher, "search")
        assert callable(searcher.search)


# ============================================================================
# BlueSkySearcher Compliance Tests (5 tests)
# ============================================================================


class TestBlueSkySearcherCompliance:
    """Test that BlueSkySearcher properly implements BaseSearcher."""

    def test_bluesky_searcher_is_base_searcher(self):
        """Test that BlueSkySearcher is a BaseSearcher."""
        assert issubclass(BlueSkySearcher, BaseSearcher)

    def test_bluesky_searcher_can_be_instantiated(self):
        """Test that BlueSkySearcher can be instantiated."""
        searcher = BlueSkySearcher()
        assert isinstance(searcher, BaseSearcher)

    def test_bluesky_searcher_has_platform_name_property(self):
        """Test that BlueSkySearcher has platform_name property."""
        searcher = BlueSkySearcher()
        assert hasattr(searcher, "platform_name")

    def test_bluesky_searcher_platform_name_returns_string(self):
        """Test that platform_name returns a string."""
        searcher = BlueSkySearcher()
        assert isinstance(searcher.platform_name, str)
        assert searcher.platform_name == "bluesky"

    @pytest.mark.asyncio
    async def test_bluesky_searcher_search_method_exists(self):
        """Test that BlueSkySearcher implements search method."""
        searcher = BlueSkySearcher()
        assert hasattr(searcher, "search")
        assert callable(searcher.search)


# ============================================================================
# ResultAnalyzer Compliance Tests (4 tests)
# ============================================================================


class TestResultAnalyzerCompliance:
    """Test that ResultAnalyzer properly implements analysis functionality."""

    def test_result_analyzer_can_be_instantiated(self):
        """Test that ResultAnalyzer can be instantiated."""
        analyzer = ResultAnalyzer()
        assert analyzer is not None

    @pytest.mark.asyncio
    async def test_result_analyzer_analyze_method_exists(self):
        """Test that ResultAnalyzer implements analyze method."""
        analyzer = ResultAnalyzer()
        assert hasattr(analyzer, "analyze")
        assert callable(analyzer.analyze)

    @pytest.mark.asyncio
    async def test_result_analyzer_analyze_returns_tuple(self):
        """Test that analyze returns a tuple."""
        analyzer = ResultAnalyzer()
        claim = ExtractedClaim(
            claim_text="test", extracted_from="text", confidence=1.0, raw_input_type="text_only"
        )
        result = await analyzer.analyze(claim, [])
        assert isinstance(result, tuple)
        assert len(result) == 3


# ============================================================================
# ResponseGenerator Compliance Tests (4 tests)
# ============================================================================


class TestResponseGeneratorCompliance:
    """Test that ResponseGenerator properly implements response generation."""

    def test_response_generator_can_be_instantiated(self):
        """Test that ResponseGenerator can be instantiated."""
        generator = ResponseGenerator()
        assert generator is not None

    @pytest.mark.asyncio
    async def test_response_generator_generate_method_exists(self):
        """Test that ResponseGenerator implements generate method."""
        generator = ResponseGenerator()
        assert hasattr(generator, "generate")
        assert callable(generator.generate)

    @pytest.mark.asyncio
    async def test_response_generator_generate_returns_dict(self):
        """Test that generate returns a dict."""
        from factchecker.core.models import VerdictEnum
        
        generator = ResponseGenerator()
        claim = ExtractedClaim(
            claim_text="test", extracted_from="text", confidence=1.0, raw_input_type="text_only"
        )
        result = await generator.generate(
            claim=claim,
            results=[],
            verdict=VerdictEnum.UNCLEAR,
            confidence=0.5,
            explanation="test"
        )
        assert isinstance(result, dict)


# ============================================================================
# Contract Validation Tests (8 tests)
# ============================================================================


class TestContractValidation:
    """Test that implementations satisfy interface contracts."""

    @pytest.mark.asyncio
    async def test_extractor_contract_signature(self):
        """Test that extractor extract() has correct signature."""
        extractor = TextExtractor()
        sig = inspect.signature(extractor.extract)
        params = list(sig.parameters.keys())
        assert "claim_text" in params
        assert "image_data" in params

    @pytest.mark.asyncio
    async def test_searcher_contract_signature(self):
        """Test that searcher search() has correct signature."""
        searcher = TwitterSearcher()
        sig = inspect.signature(searcher.search)
        params = list(sig.parameters.keys())
        assert "claim" in params
        assert "query_params" in params

    @pytest.mark.asyncio
    async def test_analyzer_contract_signature(self):
        """Test that analyzer analyze() has correct signature."""
        analyzer = ResultAnalyzer()
        sig = inspect.signature(analyzer.analyze)
        params = list(sig.parameters.keys())
        assert "claim" in params
        assert "results" in params

    def test_multiple_extractors_satisfy_contract(self):
        """Test that both extractor implementations satisfy contract."""
        extractors = [TextExtractor(), ImageExtractor()]
        for extractor in extractors:
            assert isinstance(extractor, BaseExtractor)
            assert hasattr(extractor, "extract")

    def test_multiple_searchers_satisfy_contract(self):
        """Test that both searcher implementations satisfy contract."""
        searchers = [TwitterSearcher(), BlueSkySearcher()]
        for searcher in searchers:
            assert isinstance(searcher, BaseSearcher)
            assert hasattr(searcher, "search")
            assert hasattr(searcher, "platform_name")

    def test_processor_implementations_can_be_instantiated(self):
        """Test that processor implementations can be instantiated."""
        analyzer = ResultAnalyzer()
        generator = ResponseGenerator()
        assert analyzer is not None
        assert generator is not None

    def test_searchers_have_unique_platform_names(self):
        """Test that different searchers have different platform names."""
        twitter = TwitterSearcher()
        bluesky = BlueSkySearcher()
        assert twitter.platform_name != bluesky.platform_name
        assert twitter.platform_name == "twitter"
        assert bluesky.platform_name == "bluesky"

    @pytest.mark.asyncio
    async def test_all_async_methods_are_coroutines(self):
        """Test that interface methods are async."""
        extractor = TextExtractor()
        searcher = TwitterSearcher()
        analyzer = ResultAnalyzer()

        # Extract method is async
        result = extractor.extract("test", None)
        assert inspect.iscoroutine(result)
        await result

        # Search method is async
        result = searcher.search("test", {})
        assert inspect.iscoroutine(result)
        await result

        # Analyze method is async
        claim = ExtractedClaim(
            claim_text="test", extracted_from="text", confidence=1.0, raw_input_type="text_only"
        )
        result = analyzer.analyze(claim, [])
        assert inspect.iscoroutine(result)
        await result


# ============================================================================
# Dependency Injection Tests (5 tests)
# ============================================================================


class TestDependencyInjection:
    """Test that abstract types can be used for dependency injection."""

    def test_extractor_can_be_injected_as_base_type(self):
        """Test that concrete extractor can be used as BaseExtractor."""
        extractor: BaseExtractor = TextExtractor()
        assert isinstance(extractor, BaseExtractor)

    def test_searcher_can_be_injected_as_base_type(self):
        """Test that concrete searcher can be used as BaseSearcher."""
        searcher: BaseSearcher = TwitterSearcher()
        assert isinstance(searcher, BaseSearcher)

    def test_analyzer_and_generator_can_be_instantiated(self):
        """Test that result analyzer and response generator can be instantiated."""
        analyzer = ResultAnalyzer()
        generator = ResponseGenerator()
        assert analyzer is not None
        assert generator is not None

    def test_multiple_implementations_with_base_type(self):
        """Test that different implementations can be swapped via base type."""
        extractors: List[BaseExtractor] = [TextExtractor(), ImageExtractor()]
        assert len(extractors) == 2
        for ext in extractors:
            assert isinstance(ext, BaseExtractor)

    def test_factory_pattern_with_base_type(self):
        """Test factory pattern using base type."""

        def create_searcher(platform: str) -> BaseSearcher:
            if platform == "twitter":
                return TwitterSearcher()
            elif platform == "bluesky":
                return BlueSkySearcher()
            raise ValueError(f"Unknown platform: {platform}")

        twitter = create_searcher("twitter")
        bluesky = create_searcher("bluesky")

        assert isinstance(twitter, BaseSearcher)
        assert isinstance(bluesky, BaseSearcher)
        assert twitter.platform_name == "twitter"
        assert bluesky.platform_name == "bluesky"


# ============================================================================
# Method Implementation Tests (6 tests)
# ============================================================================


class TestMethodImplementations:
    """Test that concrete implementations properly override abstract methods."""

    def test_text_extractor_overrides_extract(self):
        """Test that TextExtractor overrides extract method."""
        assert "extract" in TextExtractor.__dict__

    def test_image_extractor_overrides_extract(self):
        """Test that ImageExtractor overrides extract method."""
        assert "extract" in ImageExtractor.__dict__

    def test_twitter_searcher_overrides_search(self):
        """Test that TwitterSearcher overrides search method."""
        assert "search" in TwitterSearcher.__dict__

    def test_bluesky_searcher_overrides_search(self):
        """Test that BlueSkySearcher overrides search method."""
        assert "search" in BlueSkySearcher.__dict__

    def test_result_analyzer_overrides_analyze(self):
        """Test that ResultAnalyzer overrides analyze method."""
        assert "analyze" in ResultAnalyzer.__dict__

    def test_response_generator_overrides_generate(self):
        """Test that ResponseGenerator overrides generate method."""
        assert "generate" in ResponseGenerator.__dict__


# ============================================================================
# Property Tests (4 tests)
# ============================================================================


class TestProperties:
    """Test that properties are correctly implemented."""

    def test_twitter_searcher_platform_name_is_property(self):
        """Test that platform_name is a property."""
        assert isinstance(
            inspect.getattr_static(TwitterSearcher, "platform_name"), property
        )

    def test_bluesky_searcher_platform_name_is_property(self):
        """Test that platform_name is a property."""
        assert isinstance(
            inspect.getattr_static(BlueSkySearcher, "platform_name"), property
        )

    def test_platform_name_is_read_only(self):
        """Test that platform_name cannot be set."""
        searcher = TwitterSearcher()
        with pytest.raises(AttributeError):
            searcher.platform_name = "new_value"

    def test_platform_name_values_are_strings(self):
        """Test that platform names are non-empty strings."""
        twitter = TwitterSearcher()
        bluesky = BlueSkySearcher()
        assert isinstance(twitter.platform_name, str)
        assert isinstance(bluesky.platform_name, str)
        assert len(twitter.platform_name) > 0
        assert len(bluesky.platform_name) > 0
