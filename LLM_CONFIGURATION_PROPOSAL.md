# LLM Configuration System Proposal

## Overview
Centralized, extensible configuration system for LLM API calls across the fact-checker pipeline. Multiple functions requiring LLM calls will specify a **use case identifier**, which maps to predefined fixed and variable configurations stored in a common location.

---

## Architecture

### 1. Configuration File: `core/llm_config.py`

**Purpose**: Single source of truth for all LLM-related settings.

**Contents**:
```
LLMConfig (class)
├── Use Case Definitions (registry)
│   ├── claim_extraction_from_text
│   ├── claim_extraction_from_image
│   ├── search_query_generation
│   ├── result_analysis
│   ├── response_generation
│   └── [additional use cases as needed]
│
├── For Each Use Case:
│   ├── model: str (e.g., "gemini-1.5-flash", "gemini-pro")
│   ├── provider: str (currently "google-gemini", extensible to "openai", "anthropic")
│   ├── temperature: float (0.0-1.0)
│   ├── max_output_tokens: int
│   ├── top_p: float
│   ├── system_prompt: str
│   ├── request_timeout_seconds: float
│   └── [additional params as needed]
│
└── Helper Methods:
    ├── get_config(use_case: str) → Config dict
    ├── list_available_use_cases() → List[str]
    ├── validate_config(use_case: str) → bool
    └── query_provider_options(provider: str, param: str) → List/dict
```

### 2. Provider Integration: `core/llm_provider.py`

**Purpose**: Abstraction layer for different LLM providers (initially Google Gemini, extensible).

**Contents**:
```
LLMProvider (abstract base class)
├── Methods:
│   ├── call(use_case: str, prompt: str, **kwargs) → str
│   └── get_available_options() → dict
│
GoogleGeminiProvider (implementation)
├── Uses: google-generativeai library
├── Features:
│   ├── Fetches live model list from Gemini API
│   ├── Queries API documentation for parameter ranges
│   └── Applies use-case-specific configs from LLMConfig
│
[Future providers]
└── OpenAIProvider, AnthropicProvider, etc.
```

### 3. Helper Function: `core/llm_helpers.py`

**Purpose**: Utilities for querying and validating LLM capabilities.

**Contents**:
```
Functions:
├── list_llm_options(provider: str = "google-gemini") → dict
│   └── Returns: available models, parameter ranges, supported features
│
├── validate_use_case(use_case: str) → bool
│   └── Checks if use case exists in LLMConfig
│
├── get_model_capabilities(model: str, provider: str) → dict
│   └── Queries provider's API for real-time model capabilities
│
└── suggest_config_updates(provider: str) → dict
    └── Detects deprecated models, new options, breaking changes
```

### 4. Integration Pattern: Usage in Calling Functions

**Example - TextExtractor using LLM for claim extraction**:
```python
from factchecker.core.llm_config import get_llm_config
from factchecker.core.llm_provider import get_provider

class TextExtractor:
    async def extract(self, claim_text: str) -> ExtractedClaim:
        # Get config for this use case
        config = get_llm_config("claim_extraction_from_text")
        
        # Get the provider (defaults to google-gemini)
        provider = get_provider(config["provider"])
        
        # Call LLM with config
        result = await provider.call(
            use_case="claim_extraction_from_text",
            prompt=f"Extract and segment claims from: {claim_text}"
        )
        
        return ExtractedClaim(claim_text=result, ...)
```

---

## File Structure

```
src/factchecker/core/
├── llm_config.py          # Config registry and retrieval
├── llm_provider.py        # Provider abstraction and implementations
├── llm_helpers.py         # Query helpers and validation
└── models.py              # (existing - add LLMConfig to data models if needed)
```

---

## Configuration Storage Format

### Option A: Python Dictionary (Recommended for MVP)
`core/llm_config.py` contains a hardcoded `USE_CASE_CONFIGS` dict:
```python
USE_CASE_CONFIGS = {
    "claim_extraction_from_text": {
        "model": "gemini-1.5-flash",
        "provider": "google-gemini",
        "temperature": 0.3,
        "max_output_tokens": 500,
        "top_p": 0.95,
        "system_prompt": "You are a fact-checking assistant...",
        "request_timeout_seconds": 30.0,
    },
    "search_query_generation": {
        "model": "gemini-1.5-flash",
        "provider": "google-gemini",
        "temperature": 0.1,
        "max_output_tokens": 200,
        ...
    },
    # ... additional use cases
}
```

### Option B: YAML File (Extensible for later)
`config/llm_configs.yaml` - allows runtime updates without code changes. Implementation deferred to Phase 2.

---

## Key Design Decisions

1. **Single Use Case Registry**: All use cases predefined in one place → easier maintenance and discovery
2. **Provider Abstraction**: Swap providers (Google → OpenAI) without changing calling code
3. **Runtime Option Querying**: `query_provider_options()` calls provider APIs to get live capabilities (models, supported parameters, limits)
4. **Environment-Based Selection**: Use `.env` to select active provider and override specific configs if needed
5. **Type Safety**: Use Pydantic `BaseModel` for config validation (optional enhancement)
6. **Logging**: LLM calls logged with use case, model, timing, and cost tracking (if applicable)

---

## Implementation Phases

### Phase 1 (MVP)
- [ ] Create `llm_config.py` with initial use cases and Python dict storage
- [ ] Create `llm_provider.py` with `GoogleGeminiProvider` implementation
- [ ] Create `llm_helpers.py` with basic querying functions
- [ ] Integrate into `TextExtractor` for claim extraction
- [ ] Add unit tests for config retrieval and provider calls
- [ ] Document with examples and troubleshooting

### Phase 2 (Enhancement)
- [ ] YAML config file support for runtime updates
- [ ] Additional providers (OpenAI, Anthropic)
- [ ] Cost tracking and usage monitoring
- [ ] Config validation schema (Pydantic)
- [ ] Hot reload for config changes

### Phase 3 (Production)
- [ ] Caching layer for provider capabilities
- [ ] Fallback model selection if primary fails
- [ ] A/B testing framework for model/prompt comparisons
- [ ] Admin dashboard for config management

---

## Benefits

- **Maintainability**: Single file for all LLM settings
- **Consistency**: All use cases follow same pattern
- **Flexibility**: Easy to swap models or providers
- **Discoverability**: `list_available_use_cases()` shows all options
- **Extensibility**: New providers added without breaking existing code
- **Testability**: Mock provider for unit tests
- **Observability**: Centralized logging and cost tracking

---

## Open Questions / Decisions for Review

1. **Config Storage Format**: Python dict (MVP) vs. YAML file (more flexible)?
2. **Pydantic Models**: Should we define `UseCase` and `ProviderConfig` Pydantic models for validation?
3. **Fallback Behavior**: If primary model unavailable, should system auto-fallback to secondary model?
4. **Cost Tracking**: Should we implement usage/cost tracking from the start?
5. **Async vs Sync**: All LLM calls async (consistent with codebase) or allow sync wrappers?
