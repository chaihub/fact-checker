"""
LLM Configuration System - Central Registry

Provides a single source of truth for all LLM-related configurations across
the fact-checker pipeline. All calling functions specify a use case identifier,
which maps to predefined fixed and variable configurations stored here.

Currently supports Google Gemini API; extensible to other providers.
"""

from typing import Any

# Central registry of use case configurations
USE_CASE_CONFIGS: dict[str, dict[str, Any]] = {
    "claim_extraction_from_text": {
        "model": "gemini-2.5-flash",
        "provider": "google-gemini",
        "temperature": 0.2,
        "max_output_tokens": 800,
        "top_p": 0.95,
        "system_prompt": (
            "You are a fact-checking assistant. Your task is to analyze the given text and "
            "decompose it into claim elements. Extract ONLY the following JSON structure, "
            "with NO additional text, NO markdown, NO code blocks:\n\n"
            "{\n"
            "  \"who\": {\"value\": \"<entity or person>\", \"confidence\": 0.9, \"is_ambiguous\": false, \"is_unknown\": false},\n"
            "  \"what\": {\"value\": \"<action or event>\", \"confidence\": 0.9, \"is_ambiguous\": false, \"is_unknown\": false},\n"
            "  \"when\": {\"value\": \"<time>\", \"confidence\": 0.9, \"is_ambiguous\": false, \"is_unknown\": true},\n"
            "  \"where\": {\"value\": \"<location>\", \"confidence\": 0.9, \"is_ambiguous\": false, \"is_unknown\": true},\n"
            "  \"how\": {\"value\": \"<method>\", \"confidence\": 0.9, \"is_ambiguous\": false, \"is_unknown\": true},\n"
            "  \"why\": {\"value\": \"<reason>\", \"confidence\": 0.9, \"is_ambiguous\": false, \"is_unknown\": true},\n"
            "  \"key_assertions\": [\"assertion 1\", \"assertion 2\"],\n"
            "  \"overall_confidence\": 0.85,\n"
            "  \"reasoning\": \"brief explanation\"\n"
            "}\n\n"
            "Rules:\n"
            "- Return ONLY valid JSON, nothing else\n"
            "- Set is_unknown=true if element cannot be determined from text\n"
            "- Set is_ambiguous=true if element is unclear\n"
            "- confidence should be 0-1 for each element\n"
            "- key_assertions should be 2-4 verifiable claims"
        ),
        "request_timeout_seconds": 30.0,
    },
    "claim_extraction_from_image": {
        "model": "gemini-2.5-flash",
        "provider": "google-gemini",
        "temperature": 0.2,
        "max_output_tokens": 1000,
        "top_p": 0.9,
        "system_prompt": (
            "You are a fact-checking assistant. Your task is to extract and "
            "structure claims from OCR'd image text. Use multiple questions "
            "(who, what, when, where, why) to deeply understand the content. "
            "Return a JSON response with structured claims and confidence scores."
        ),
        "request_timeout_seconds": 45.0,
    },
    "search_query_generation": {
        "model": "gemini-2.5-flash",
        "provider": "google-gemini",
        "temperature": 0.1,
        "max_output_tokens": 200,
        "top_p": 0.95,
        "system_prompt": (
            "You are a search optimization assistant. Your task is to generate "
            "optimized search queries from claims for fact-checking. Create "
            "multiple query variations for redundancy. "
            "Return a JSON response with 'queries' array and priority scores."
        ),
        "request_timeout_seconds": 20.0,
    },
    "result_analysis": {
        "model": "gemini-2.5-flash",
        "provider": "google-gemini",
        "temperature": 0.5,
        "max_output_tokens": 300,
        "top_p": 0.9,
        "system_prompt": (
            "You are a fact-checking analyst. Your task is to analyze search "
            "results and determine if they support, contradict, or are neutral "
            "regarding the claim. Provide a verdict with confidence score. "
            "Return a JSON response with 'verdict' and 'confidence'."
        ),
        "request_timeout_seconds": 30.0,
    },
    "response_generation": {
        "model": "gemini-2.5-flash",
        "provider": "google-gemini",
        "temperature": 0.7,
        "max_output_tokens": 800,
        "top_p": 0.95,
        "system_prompt": (
            "You are a fact-check report generator. Your task is to generate "
            "clear, human-readable fact-check responses. Provide a verdict, "
            "explanation, and evidence summary. Be concise and accessible. "
            "Return a JSON response with 'verdict', 'explanation', and 'evidence'."
        ),
        "request_timeout_seconds": 30.0,
    },
}


def get_llm_config(use_case: str) -> dict[str, Any]:
    """
    Retrieve configuration for a specific LLM use case.

    Args:
        use_case: Identifier for the use case (e.g., "claim_extraction_from_text")

    Returns:
        Dictionary containing use case configuration

    Raises:
        ValueError: If use case is not found in registry
    """
    if use_case not in USE_CASE_CONFIGS:
        available = ", ".join(list_available_use_cases())
        raise ValueError(
            f"Unknown use case: {use_case}. "
            f"Available use cases: {available}"
        )
    return USE_CASE_CONFIGS[use_case].copy()


def list_available_use_cases() -> list[str]:
    """
    List all available LLM use case identifiers.

    Returns:
        Sorted list of use case identifiers
    """
    return sorted(USE_CASE_CONFIGS.keys())


def validate_config(use_case: str) -> bool:
    """
    Validate if a use case exists and has required configuration fields.

    Args:
        use_case: Use case identifier to validate

    Returns:
        True if use case is valid, False otherwise
    """
    if use_case not in USE_CASE_CONFIGS:
        return False

    config = USE_CASE_CONFIGS[use_case]
    required_fields = {
        "model",
        "provider",
        "temperature",
        "max_output_tokens",
        "top_p",
        "system_prompt",
        "request_timeout_seconds",
    }

    return all(field in config for field in required_fields)
