# Implementation Plan: External Sources Configuration & Registry

## Overview
Create a hardcoded external sources registry that enables `_verify_claims()` to dynamically instantiate and call the appropriate searchers by key. The registry maps source keys to metadata (category, class name) needed for dynamic instantiation.

## Design Decisions

### 1. Data Structure: Source Registry
**Location**: `src/factchecker/core/sources_config.py` (new file)

**Components**:

- **SourceCategory Enum** (3-char codes):
  - `SOC` = Social Media (Twitter, BlueSky, etc.)
  - `NWS` = News/Commercial Media
  - `GOV` = Government/Official
  - `OTH` = Other/Academic/Research

- **SourceConfig Model** (Pydantic):
  - `category: SourceCategory` — Classification
  - `class_name: str` — Name of searcher class to instantiate
  - `display_name: str` — Human-readable name (for logging/UI)
  - **Note**: `platform` identifier is the dict key, not duplicated in the model

- **EXTERNAL_SOURCES Registry** (dict):
  ```python
  EXTERNAL_SOURCES: dict[str, SourceConfig] = {
      "twitter": SourceConfig(
          category=SourceCategory.SOC,
          class_name="TwitterSearcher",
          display_name="Twitter"
      ),
      "bluesky": SourceConfig(
          category=SourceCategory.SOC,
          class_name="BlueSkySearcher",
          display_name="BlueSky"
      ),
      "news": SourceConfig(
          category=SourceCategory.NWS,
          class_name="NewsSearcher",
          display_name="News"
      ),
      "gov": SourceConfig(
          category=SourceCategory.GOV,
          class_name="GovernmentSearcher",
          display_name="Government"
      ),
  }
  ```
  - Dict key is the platform identifier (used as `SearchResult.external_source`)
  - SourceConfig holds only metadata (no key duplication)
  - One entry per category; add more sources within same category as needed

### 2. Instantiation Function
**Location**: Same file (`sources_config.py`)

**Function**: `get_searcher(platform: str) -> BaseSearcher`
- Takes source platform identifier (dict key from registry)
- Dynamically imports and instantiates the searcher class from `factchecker.searchers` module
- Returns instance ready to call `.search()`
- Raises `SourceNotFoundError` if platform not in registry or import fails

### 3. Integration Point
**Location**: `src/factchecker/pipeline/factcheck_pipeline.py`

**Usage in `_verify_claims()`**:
- Iterate over desired sources (logic TBD)
- Call `get_searcher(platform)` to instantiate
- Call `.search(claim_text, query_params)` on instance
- Collect results with platform matching source platform identifier

### 4. Consistency Guarantee
- Registry dict key (platform identifier) matches `SearchResult.platform` in all results
- Example: EXTERNAL_SOURCES["twitter"] → all Twitter results have `platform="twitter"`
- Automatic alignment—no duplication means no mismatch possible

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/factchecker/core/sources_config.py` | **Create** | Registry, enum, SourceConfig model, instantiation logic |
| `src/factchecker/core/models.py` | Modify | Rename `SearchResult.platform` to `SearchResult.external_source` |
| `src/factchecker/core/interfaces.py` | Modify | Add custom exception `SourceNotFoundError` or use existing pattern |
| `src/factchecker/searchers/twitter_searcher.py` | Modify | Update mock/real results to use `external_source` instead of `platform` |
| `src/factchecker/searchers/bluesky_searcher.py` | Modify | Update mock/real results to use `external_source` instead of `platform` |
| `src/factchecker/searchers/news_searcher.py` | **Create** | NewsSearcher class (NWS category) following TwitterSearcher pattern |
| `src/factchecker/searchers/government_searcher.py` | **Create** | GovernmentSearcher class (GOV category) following TwitterSearcher pattern |
| `src/factchecker/pipeline/factcheck_pipeline.py` | Modify | Import registry; update `_verify_claims()` stub to use it (logic details TBD) |

## Success Criteria
- [x] SourceCategory enum with 3-char codes defined and used
- [x] SourceConfig model created with required fields (no key duplication)
- [x] EXTERNAL_SOURCES registry hardcoded with 1 source per category (Twitter, BlueSky, News, Gov)
- [x] Dynamic instantiation function tested and working
- [x] SearchResult.platform renamed to SearchResult.external_source
- [x] TwitterSearcher and BlueSkySearcher updated to use external_source in results
- [x] NewsSearcher class created (pattern: TwitterSearcher, returns News/Media results)
- [x] GovernmentSearcher class created (pattern: TwitterSearcher, returns Government results)
- [x] Registry dict keys match external_source in all mock/real results
- [x] Pipeline can import and use get_searcher() without errors

## Notes
- Rate limiting, ordering, filtering per source deferred to `_verify_claims()` logic implementation
- Query formatting per source handled within individual searcher classes
- API key management out of scope (handled elsewhere)
