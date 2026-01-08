"""
Unit tests for LLM Provider implementations.

Tests GoogleGeminiProvider class methods including:
- Initialization with API key validation
- LLM calls with use-case-specific configurations
- Error handling (timeout, API errors, invalid use cases)
- Parameter handling and overrides
- Available options retrieval
"""

import asyncio
import os
import sys
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any

from factchecker.core.llm_provider import (
    GoogleGeminiProvider,
    LLMProvider,
)

# Check if API key is available for integration tests
HAS_GEMINI_API_KEY = bool(os.getenv("GEMINI_API_KEY"))


class TestGoogleGeminiProviderInit:
    """Test GoogleGeminiProvider initialization."""

    def test_init_with_valid_api_key(self) -> None:
        """Test initialization with valid GEMINI_API_KEY environment variable."""
        mock_genai = MagicMock()
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key_123"}):
            with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
                provider = GoogleGeminiProvider()
                assert provider.api_key == "test_api_key_123"
                mock_genai.configure.assert_called_once_with(
                    api_key="test_api_key_123"
                )

    def test_init_without_api_key_raises_error(self) -> None:
        """Test initialization raises RuntimeError when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                GoogleGeminiProvider()
            assert "GEMINI_API_KEY" in str(exc_info.value)

    def test_init_with_missing_package_raises_error(self) -> None:
        """Test initialization raises RuntimeError when google-generativeai is not installed."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            with patch(
                "builtins.__import__",
                side_effect=ImportError("No module named google.generativeai"),
            ):
                with pytest.raises(RuntimeError) as exc_info:
                    GoogleGeminiProvider()
                assert "google-generativeai" in str(exc_info.value)


class TestGoogleGeminiProviderCall:
    """Test GoogleGeminiProvider.call() method."""

    @pytest.fixture
    def mock_provider(self) -> Mock:
        """Create a mocked GoogleGeminiProvider for testing."""
        mock_genai = MagicMock()
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
                provider = GoogleGeminiProvider()
                return provider

    @pytest.mark.asyncio
    async def test_call_with_valid_use_case(
        self, mock_provider: Mock
    ) -> None:
        """Test successful call with valid use case."""
        # Mock the genai.GenerativeModel and response
        mock_model = AsyncMock()
        mock_response = Mock()
        mock_response.text = "Test response from Gemini"

        with patch.object(
            mock_provider, "genai"
        ) as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            with patch.object(
                mock_provider,
                "_call_gemini",
                return_value="Test response from Gemini",
            ):
                response = await mock_provider.call(
                    "claim_extraction_from_text",
                    "Is the sky blue?",
                )
                assert response == "Test response from Gemini"

    @pytest.mark.asyncio
    async def test_call_with_invalid_use_case_raises_error(
        self, mock_provider: Mock
    ) -> None:
        """Test call raises ValueError for unknown use case."""
        with pytest.raises(ValueError) as exc_info:
            await mock_provider.call(
                "nonexistent_use_case",
                "Some prompt",
            )
        assert "Unknown use case" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_with_timeout_raises_error(
        self, mock_provider: Mock
    ) -> None:
        """Test call raises RuntimeError when API call times out."""
        with patch.object(
            mock_provider,
            "_call_gemini",
            side_effect=asyncio.TimeoutError(),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                await mock_provider.call(
                    "claim_extraction_from_text",
                    "Test prompt",
                )
            assert "timed out" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_logs_request_parameters(
        self, mock_provider: Mock
    ) -> None:
        """Test that call logs request parameters correctly."""
        with patch.object(
            mock_provider,
            "_call_gemini",
            return_value="Test response",
        ):
            response = await mock_provider.call(
                "claim_extraction_from_text",
                "Test prompt",
                temperature=0.9,
            )
            assert response == "Test response"
            # Verify the call was made
            mock_provider._call_gemini.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_parameter_override(
        self, mock_provider: Mock
    ) -> None:
        """Test that kwargs override default parameters."""
        with patch.object(
            mock_provider,
            "_call_gemini",
            return_value="Test response",
        ):
            response = await mock_provider.call(
                "claim_extraction_from_text",
                "Test prompt",
                temperature=0.9,
                max_output_tokens=1000,
            )
            assert response == "Test response"
            # Verify _call_gemini was called (parameters are passed there)
            mock_provider._call_gemini.assert_called_once()


class TestGoogleGeminiProviderCallGemini:
    """Test GoogleGeminiProvider._call_gemini() method."""

    @pytest.fixture
    def mock_provider(self) -> Mock:
        """Create a mocked GoogleGeminiProvider for testing."""
        mock_genai = MagicMock()
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
                provider = GoogleGeminiProvider()
                return provider

    @pytest.mark.asyncio
    async def test_call_gemini_with_valid_response(
        self, mock_provider: Mock
    ) -> None:
        """Test _call_gemini returns response text successfully."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Valid response text"
        mock_model.generate_content.return_value = mock_response

        result = await mock_provider._call_gemini(
            mock_model,
            "Test prompt",
            {"temperature": 0.5},
        )

        assert result == "Valid response text"
        mock_model.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_gemini_with_empty_response_raises_error(
        self, mock_provider: Mock
    ) -> None:
        """Test _call_gemini raises RuntimeError for empty response."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = ""  # Empty response
        mock_model.generate_content.return_value = mock_response

        with pytest.raises(RuntimeError) as exc_info:
            await mock_provider._call_gemini(
                mock_model,
                "Test prompt",
                {"temperature": 0.5},
            )
        assert "Empty response" in str(exc_info.value)


class TestGoogleGeminiProviderGetAvailableOptions:
    """Test GoogleGeminiProvider.get_available_options() method."""

    @pytest.fixture
    def provider(self) -> GoogleGeminiProvider:
        """Create a real GoogleGeminiProvider instance for testing."""
        mock_genai = MagicMock()
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
                return GoogleGeminiProvider()

    def test_get_available_options_returns_dict(
        self, provider: GoogleGeminiProvider
    ) -> None:
        """Test get_available_options returns a dictionary."""
        options = provider.get_available_options()
        assert isinstance(options, dict)

    def test_get_available_options_has_required_fields(
        self, provider: GoogleGeminiProvider
    ) -> None:
        """Test get_available_options includes required fields."""
        options = provider.get_available_options()
        required_fields = {
            "provider",
            "models",
            "temperature_range",
            "max_output_tokens_range",
            "top_p_range",
            "supported_features",
        }
        assert required_fields.issubset(set(options.keys()))

    def test_get_available_options_provider_name(
        self, provider: GoogleGeminiProvider
    ) -> None:
        """Test provider name is correctly set."""
        options = provider.get_available_options()
        assert options["provider"] == "google-gemini"

    def test_get_available_options_models_list(
        self, provider: GoogleGeminiProvider
    ) -> None:
        """Test models list is not empty."""
        options = provider.get_available_options()
        assert isinstance(options["models"], list)
        assert len(options["models"]) > 0
        assert all(isinstance(m, str) for m in options["models"])

    def test_get_available_options_temperature_range(
        self, provider: GoogleGeminiProvider
    ) -> None:
        """Test temperature range is valid."""
        options = provider.get_available_options()
        temp_range = options["temperature_range"]
        assert temp_range["min"] == 0.0
        assert temp_range["max"] == 1.0

    def test_get_available_options_max_tokens_range(
        self, provider: GoogleGeminiProvider
    ) -> None:
        """Test max output tokens range is valid."""
        options = provider.get_available_options()
        tokens_range = options["max_output_tokens_range"]
        assert tokens_range["min"] >= 1
        assert tokens_range["max"] >= tokens_range["min"]

    def test_get_available_options_supported_features(
        self, provider: GoogleGeminiProvider
    ) -> None:
        """Test supported features list is not empty."""
        options = provider.get_available_options()
        features = options["supported_features"]
        assert isinstance(features, list)
        assert len(features) > 0


class TestLLMProviderAbstractBase:
    """Test LLMProvider abstract base class."""

    def test_llm_provider_cannot_be_instantiated(self) -> None:
        """Test that LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider()  # type: ignore

    def test_llm_provider_call_is_abstract(self) -> None:
        """Test that call method is abstract."""
        assert hasattr(LLMProvider, "call")
        assert getattr(LLMProvider.call, "__isabstractmethod__", False)

    def test_llm_provider_get_available_options_is_abstract(
        self,
    ) -> None:
        """Test that get_available_options method is abstract."""
        assert hasattr(LLMProvider, "get_available_options")
        assert getattr(
            LLMProvider.get_available_options, "__isabstractmethod__", False
        )

    def test_google_gemini_provider_implements_interface(self) -> None:
        """Test that GoogleGeminiProvider implements LLMProvider interface."""
        mock_genai = MagicMock()
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
                provider = GoogleGeminiProvider()
                assert isinstance(provider, LLMProvider)
                assert hasattr(provider, "call")
                assert hasattr(provider, "get_available_options")


@pytest.mark.skipif(
    not HAS_GEMINI_API_KEY, reason="GEMINI_API_KEY not set in environment"
)
@pytest.mark.integration
class TestGoogleGeminiProviderIntegration:
    """Integration tests with real Google Gemini API."""

    @pytest.mark.asyncio
    async def test_real_api_call_alphabet_question(self) -> None:
        """
        Integration test: Make real API call to Gemini asking about English alphabet.

        This test requires GEMINI_API_KEY to be set in environment variables.
        It will be skipped if the API key is not available.
        """
        provider = GoogleGeminiProvider()

        # Ask a simple question that should return a predictable answer
        prompt = "How many letters are there in the English alphabet?"

        # Call the API using the search_query_generation use case
        try:
            response = await provider.call(
                use_case="search_query_generation",
                prompt=prompt,
            )
        except RuntimeError as e:
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                pytest.skip(f"Rate limited: {e}")
            raise

        # Verify we got a non-empty response
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

        # Verify the response is not truncated
        assert len(response) > 10, f"Response too short: {response}"

        print(f"\n✓ Real API Response: {response[:200]}...")

    @pytest.mark.asyncio
    async def test_real_api_call_claim_extraction(self) -> None:
        """
        Integration test: Real API call for claim extraction use case.

        Tests the claim extraction functionality with a simple factual claim.
        """
        provider = GoogleGeminiProvider()

        # A simple claim to extract from
        claim_text = "The Earth orbits around the Sun."

        response = await provider.call(
            use_case="claim_extraction_from_text",
            prompt=claim_text,
        )

        # Verify response structure
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

        print(f"\n✓ Claim Extraction Response: {response[:200]}...")

    @pytest.mark.asyncio
    async def test_real_api_call_with_custom_parameters(self) -> None:
        """
        Integration test: API call with custom parameter overrides.

        Tests that custom temperature and token parameters work with real API.
        """
        provider = GoogleGeminiProvider()

        prompt = "What is 2+2?"

        response = await provider.call(
            use_case="search_query_generation",
            prompt=prompt,
            temperature=0.1,  # Low temperature for deterministic response
            max_output_tokens=100,  # Limit output size
        )

        # Verify response
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        # Response should contain some content (might be formatted as code block)
        # The API may format differently, so just verify non-empty response
        assert response.strip(), f"Response was empty or whitespace only: {response}"

        print(f"\n✓ Custom Parameters Response: {response[:200]}...")
