"""
LLM Provider Abstraction Layer

Provides abstract base class and concrete implementations for LLM API calls.
Currently implements Google Gemini provider; extensible to OpenAI, Anthropic, etc.

All calls are async to support concurrent execution and comply with FastAPI patterns.
"""

import asyncio
import os
from abc import ABC, abstractmethod
from typing import Any

from factchecker.core.llm_config import get_llm_config
from factchecker.logging_config import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def call(
        self, use_case: str, prompt: str, **kwargs: Any
    ) -> str:
        """
        Execute an LLM call for a specific use case.

        Args:
            use_case: Use case identifier from llm_config
            prompt: Input prompt/request text
            **kwargs: Additional parameters to pass to the API

        Returns:
            Response text from the LLM

        Raises:
            ValueError: If use case is not found
            RuntimeError: If API call fails
        """
        pass

    @abstractmethod
    def get_available_options(self) -> dict[str, Any]:
        """
        Get available models and configuration options from the provider.

        Returns:
            Dictionary with available models, parameters, and limits
        """
        pass


class GoogleGeminiProvider(LLMProvider):
    """Google Gemini LLM Provider implementation."""

    def __init__(self) -> None:
        """Initialize Google Gemini provider with API key from environment."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable not set. "
                "Please set it before using GoogleGeminiProvider."
            )

        try:
            import google.generativeai as genai

            self.genai = genai
            genai.configure(api_key=self.api_key)
        except ImportError as e:
            raise RuntimeError(
                "google-generativeai package not installed. "
                "Install it with: pip install google-generativeai"
            ) from e

        logger.info("GoogleGeminiProvider initialized successfully")

    async def call(
        self, use_case: str, prompt: str, **kwargs: Any
    ) -> str:
        """
        Call Google Gemini API with use-case-specific configuration.

        Args:
            use_case: Use case identifier from llm_config
            prompt: Input prompt
            **kwargs: Additional parameters (override defaults if needed)

        Returns:
            Response text from Gemini

        Raises:
            ValueError: If use case is unknown
            RuntimeError: If API call fails
        """
        # Get configuration for this use case
        config = get_llm_config(use_case)

        # Log the call
        logger.info(
            "LLM call initiated",
            extra={
                "use_case": use_case,
                "model": config["model"],
                "prompt_length": len(prompt),
            },
        )

        try:
            # Prepare request parameters
            request_params = {
                "temperature": config.get("temperature", 0.7),
                "top_p": config.get("top_p", 0.95),
                "max_output_tokens": config.get("max_output_tokens", 500),
            }

            # Override with any kwargs passed in
            request_params.update(kwargs)

            # Create the model instance
            model = self.genai.GenerativeModel(
                model_name=config["model"],
                system_instruction=config.get("system_prompt", ""),
            )

            # Execute in thread pool to avoid blocking
            timeout = config.get("request_timeout_seconds", 30.0)
            response = await asyncio.wait_for(
                self._call_gemini(model, prompt, request_params),
                timeout=timeout,
            )

            logger.info(
                "LLM call completed successfully",
                extra={
                    "use_case": use_case,
                    "response_length": len(response),
                },
            )

            return response

        except asyncio.TimeoutError as e:
            logger.error(
                "LLM API call timed out",
                extra={"use_case": use_case},
                exc_info=True,
            )
            raise RuntimeError(
                f"LLM call timed out for use case: {use_case}"
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error in LLM call",
                extra={"use_case": use_case, "error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(f"LLM call failed: {str(e)}") from e

    async def _call_gemini(
        self,
        model: Any,
        prompt: str,
        request_params: dict[str, Any],
    ) -> str:
        """
        Execute Gemini API call in thread pool to avoid blocking.

        Args:
            model: Gemini model instance
            prompt: Input prompt
            request_params: Request configuration parameters

        Returns:
            Response text
        """
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                prompt,
                generation_config=self.genai.types.GenerationConfig(
                    **request_params
                ),
            ),
        )

        if not response.text:
            raise RuntimeError("Empty response from Gemini API")

        return response.text

    def get_available_options(self) -> dict[str, Any]:
        """
        Get available models and options from Google Gemini.

        Returns:
            Dictionary with available models and configuration options
        """
        return {
            "provider": "google-gemini",
            "models": [
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
            ],
            "temperature_range": {"min": 0.0, "max": 1.0},
            "max_output_tokens_range": {"min": 1, "max": 8000},
            "top_p_range": {"min": 0.0, "max": 1.0},
            "supported_features": [
                "text-generation",
                "vision",
                "system-instructions",
            ],
        }
