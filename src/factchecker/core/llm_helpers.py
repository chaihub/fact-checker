"""
LLM Helper Utilities

Provides utility functions for querying LLM provider capabilities,
validating configurations, and managing model options.
"""

from typing import Any

from factchecker.core.llm_config import (
    list_available_use_cases,
    validate_config,
)
from factchecker.core.llm_provider import GoogleGeminiProvider
from factchecker.logging_config import get_logger

logger = get_logger(__name__)


def list_llm_options(provider: str = "google-gemini") -> dict[str, Any]:
    """
    List available LLM options and capabilities for a provider.

    Google Gemini model capabilities: https://ai.google.dev/gemini-api/docs/models#gemini-2.5-flash-image
    Google Gemini model pricing & limits: https://ai.google.dev/gemini-api/docs/pricing

    Args:
        provider: Provider name (default: "google-gemini")

    Returns:
        Dictionary with available models, parameters, and ranges

    Raises:
        ValueError: If provider is not supported
    """
    if provider == "google-gemini":
        try:
            gemini_provider = GoogleGeminiProvider()
            options = gemini_provider.get_available_options()
            logger.info(
                f"Retrieved LLM options for provider: {provider}",
                extra={"models_count": len(options.get("models", []))},
            )
            return options
        except RuntimeError as e:
            logger.warning(
                f"Could not initialize provider {provider}: {str(e)}"
            )
            raise ValueError(f"Provider {provider} not available: {str(e)}") from e
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: google-gemini"
        )


def validate_use_case(use_case: str) -> bool:
    """
    Validate if a use case exists in the configuration.

    Args:
        use_case: Use case identifier to validate

    Returns:
        True if use case is valid and properly configured, False otherwise
    """
    is_valid = validate_config(use_case)
    if not is_valid:
        logger.debug(f"Validation failed for use case: {use_case}")
    else:
        logger.debug(f"Use case validated: {use_case}")
    return is_valid


def get_model_capabilities(
    model: str, provider: str = "google-gemini"
) -> dict[str, Any]:
    """
    Get real-time capabilities and limits for a specific model.

    Args:
        model: Model name (e.g., "gemini-1.5-flash")
        provider: Provider name (default: "google-gemini")

    Returns:
        Dictionary with model capabilities and limits

    Raises:
        ValueError: If model not found or provider not supported
    """
    try:
        options = list_llm_options(provider)
        if model not in options.get("models", []):
            available = ", ".join(options.get("models", []))
            raise ValueError(
                f"Model {model} not found. "
                f"Available models: {available}"
            )

        # Return model-specific capabilities
        capabilities = {
            "model": model,
            "provider": provider,
            "supports_vision": "vision" in options.get("supported_features", []),
            "supports_system_instructions": "system-instructions"
            in options.get("supported_features", []),
            "temperature_range": options.get("temperature_range", {}),
            "max_output_tokens_range": options.get("max_output_tokens_range", {}),
            "top_p_range": options.get("top_p_range", {}),
        }

        logger.info(
            f"Retrieved capabilities for model: {model}",
            extra={"provider": provider},
        )
        return capabilities

    except ValueError as e:
        logger.error(f"Error getting model capabilities: {str(e)}")
        raise


def suggest_config_updates(provider: str = "google-gemini") -> dict[str, Any]:
    """
    Suggest configuration updates based on provider's current capabilities.

    Detects deprecated models, new available models, and other changes.

    Args:
        provider: Provider name to check

    Returns:
        Dictionary with suggestions and potential issues

    Raises:
        ValueError: If provider not supported
    """
    try:
        options = list_llm_options(provider)
        use_cases = list_available_use_cases()

        issues = []
        suggestions = []

        # Check each configured use case
        for use_case in use_cases:
            from factchecker.core.llm_config import get_llm_config

            config = get_llm_config(use_case)
            model = config.get("model")
            config_provider = config.get("provider")

            if config_provider != provider:
                continue

            # Check if model exists
            if model not in options.get("models", []):
                issues.append(
                    {
                        "type": "deprecated_model",
                        "use_case": use_case,
                        "model": model,
                        "message": f"Model {model} not found in {provider}",
                    }
                )

                # Suggest alternative
                available_models = options.get("models", [])
                if available_models:
                    suggestions.append(
                        {
                            "use_case": use_case,
                            "suggestion": f"Consider updating to {available_models[0]}",
                            "available_models": available_models,
                        }
                    )

        result = {
            "provider": provider,
            "timestamp": None,  # Could add timestamp if needed
            "issues_found": len(issues),
            "issues": issues,
            "suggestions": suggestions,
            "available_models": options.get("models", []),
        }

        if issues:
            logger.warning(
                f"Configuration issues detected for provider {provider}",
                extra={"issue_count": len(issues)},
            )
        else:
            logger.info(f"Configuration is up-to-date for provider {provider}")

        return result

    except ValueError as e:
        logger.error(f"Error checking configuration updates: {str(e)}")
        raise
