# Implementation Plan: `FactCheckPipeline._verify_claims()`

## Overview

Implement `_verify_claims()` following the workflow logic from `factchecker.drawio` Page-4 (Claim Verification).  
For each `ExtractedClaim`, the method will:
- Use decomposed **answers** (`who`, `what`, `where`, etc.) from `ClaimQuestion`
- Search external sources in a configurable default order
- Optionally reorder sources based on the `where` answer
- Stop when a match is found or all sources are checked
- Record confidence values for the claim and its components

The goal here is a **skeleton implementation plan** and structure, not full production logic.

---

## Workflow from Page-4 Diagram (Mapped to Code)

1. **Start verifying an ExtractedClaim**
2. **Check if both 'who' and 'what' claims present?**
   - **No** → Record no confidence in each claim → Done
   - **Yes** → Continue
3. **Check if 'where' claim present?**
   - **Yes** → Reorder list of sources and move the matching source to the first position
   - **No** → Continue with original source order
4. **Search using 'who' and 'what' claims in each source**, stopping when there is a match or all sources are searched
5. **Check if match found?**
   - **Yes** → Record appropriate confidence in each claim  
     (for claims other than 'who', 'what' and 'where', check search results to determine confidence) → Done
   - **No** → Record no confidence in each claim → Done

---

## Current State (Pipeline)

- **Location**: `src/factchecker/pipeline/factcheck_pipeline.py`

Current stub (simplified):

```python
@log_stage("Claim Verification")
async def _verify_claims(
    self, claims: List[ExtractedClaim]
) -> List[SearchResult]:
    """Verify each claim.
    """
    search_results: List[SearchResult] = []
    for claim in claims:
        results = await self.searcher.search(claim.claim_text)
        search_results.extend(results)

    return search_results
```

**Issues with current stub**:
- Uses `self.searcher` (singular) which does not exist (we have multiple external sources)
- Does not follow Page-4 workflow
- Does not use decomposed answers (`ClaimQuestion`)
- No source reordering based on `where`
- No configurable default search order
- No match detection logic
- No confidence recording on `ExtractedClaim` or its questions

---

## Data Structures (Relevant Models)

### `ExtractedClaim` (from `core/models.py`)

- `claim_text: str` — Full claim text
- `extracted_from: Literal["image", "text", "hybrid"]`
- `confidence: float` — Overall extraction/verification confidence
- `raw_input_type: Literal["text_only", "image_only", "both"]`
- `metadata: dict`
- `questions: List[ClaimQuestion]` — Decomposed elements (who, what, where, etc.)
- `segments: List[str]`

### `ClaimQuestion`

- `question_type: Literal["who", "when", "where", "what", "how", "why", "platform"]`
- `answer_text: str` — The answer text (this is the actual sub-claim)
- `related_entity: Optional[str]`
- `confidence: float` — Confidence for this specific answer (0–1)

### `SearchResult`

- `external_source: str` — Platform identifier (e.g., `"twitter"`, `"news"`)
- `content: str`
- `author: str`
- `url: str`
- `timestamp: datetime`
- `engagement: dict`
- `metadata: dict`

### Sources Registry (`core/sources_config.py`)

- `EXTERNAL_SOURCES: dict[str, SourceConfig]`
- Keys: `"twitter"`, `"bluesky"`, `"news"`, `"gov"`, etc.
- `SourceConfig` will include:
  - `category: SourceCategory`
  - `class_name: str`
  - `display_name: str`
  - `sequence: int` — **Numeric order** for default source ordering (lower = checked earlier)
- Use `get_searcher(platform: str) -> BaseSearcher` to instantiate an appropriate searcher.

Default source order will be derived from `sequence`, not from dict key order.

---

## Implementation Plan

### Step 1: Helper Methods (only 2)

We keep `_verify_claims()` as the main orchestrator and only extract **confidence-recording** into helpers.  
All other logic (finding answers, building queries, iterating sources, etc.) will be inline.

#### 1.1 `_record_no_confidence(claim: ExtractedClaim) -> None`

- **Purpose**: Represent the Page-4 branches “No who/what” or “No match” → “Record no confidence in each claim”.
- **Behavior (to be implemented later)**:
  - Set `claim.confidence = 0.0`
  - For every `ClaimQuestion` in `claim.questions`, set `q.confidence = 0.0`
  - Optionally add metadata explaining why (e.g., `"no_match": True`)
  - Modify `claim` in-place (no return value)

#### 1.2 `_record_confidence_from_match(claim: ExtractedClaim, search_results: List[SearchResult], match_found: bool) -> None`

- **Purpose**: Implement the “Match found?” → Yes / No logic for confidence recording.
- **Behavior (to be implemented later)**, at a high level:
  - If `match_found`:
    - For `who` and `what` (and `where` if present), set `q.confidence = 1.0`
    - For other question types (`when`, `how`, `why`, `platform`), derive confidence from `search_results` (logic TBD)
    - Derive overall `claim.confidence` from the individual question confidences (e.g., average or weighted scheme)
  - If not `match_found`:
    - Delegate to `_record_no_confidence(claim)`
  - Modify `claim` in-place.

---

### Step 2: Main `_verify_claims()` Implementation

**Note**: All logic except confidence recording will be implemented directly within `_verify_claims()`.

#### 2.1 Signature

```python
async def _verify_claims(
    self, claims: List[ExtractedClaim]
) -> List[SearchResult]:
```

#### 2.2 Logic Flow (all inline within `_verify_claims()`)

1. **Initialize results container**
   - `all_search_results: List[SearchResult] = []`

2. **Get default source order**  
   - Use the numeric `sequence` field on each `EXTERNAL_SOURCES` entry:
   - ```python
     source_order = sorted(
         EXTERNAL_SOURCES.keys(),
         key=lambda key: EXTERNAL_SOURCES[key].sequence,
     )
     ```
   - Example: If `EXTERNAL_SOURCES` sequences are `twitter=1, bluesky=2, news=3, gov=4`, then  
     `source_order == ["twitter", "bluesky", "news", "gov"]`.

3. **For each `claim` in `claims`:**

   - **3.1 Check if both 'who' and 'what' answers present**
     - Find 'who' answer:
       ```python
       who_a = next(
           (q for q in claim.questions if q.question_type == "who"),
           None,
       )
       ```
     - Find 'what' answer:
       ```python
       what_a = next(
           (q for q in claim.questions if q.question_type == "what"),
           None,
       )
       ```
     - If either `who_a` or `what_a` is `None`:
       - Call `_record_no_confidence(claim)`
       - `continue` to next claim

   - **3.2 Get 'where' answer (optional)**
     - ```python
       where_a = next(
           (q for q in claim.questions if q.question_type == "where"),
           None,
       )
       ```

   - **3.3 Determine per-claim source order**
     - Start from default: `claim_source_order = source_order.copy()`
     - If `where_a` exists:
       - Normalize: `where_answer_lower = where_a.answer_text.lower()`
       - Iterate `claim_source_order`:
         - For each `platform`:
           - Read config: `config = EXTERNAL_SOURCES[platform]`
           - If `platform.lower() == where_answer_lower` **or**  
             `config.display_name.lower() == where_answer_lower`:
             - Move this platform to index 0:
               ```python
               claim_source_order.remove(platform)
               claim_source_order.insert(0, platform)
               ```
             - `break`
       - This encodes the Page-4 “Reorder list of sources and move the given source to the first position.”

   - **3.4 Build search query and params**
     - Basic initial approach (can be refined later):
       - ```python
         search_query = f"{who_a.answer_text} {what_a.answer_text}"
         query_params = {
             "who": who_a.answer_text,
             "what": what_a.answer_text,
         }
         if where_a:
             query_params["where"] = where_a.answer_text
         ```
     - Later iterations can:
       - Normalize text
       - Add more structured params (date ranges, filters, etc.)

   - **3.5 Search each source until match found**
     - Initialize:
       - `match_found = False`
       - `claim_results: List[SearchResult] = []`
     - For each `platform` in `claim_source_order`:
       - Get searcher:
         ```python
         searcher = get_searcher(platform)
         ```
       - Execute search:
         ```python
         results = await searcher.search(search_query, query_params)
         claim_results.extend(results)
         ```
       - Check for match (simple placeholder at skeleton level):
         - For now, we keep match detection as a **TODO** inside the loop:
           ```python
           # TODO: implement actual match detection
           match_found = False  # placeholder
           ```
         - Once implemented (later), it may:
           - Compare `who_a.answer_text` with `SearchResult.author`
           - Compare `what_a.answer_text` with `SearchResult.content`
           - Use fuzzy matching / LLM-assisted scoring
       - If `match_found` becomes `True`:
         - Break the loop early (`break`)
     - After the loop:
       - Append `claim_results` to `all_search_results`

   - **3.6 Record confidence using helper**
     - ```python
       self._record_confidence_from_match(claim, claim_results, match_found)
       ```

4. **Return all search results**
   - `return all_search_results`

---

### Step 3: Imports Needed

At top of `factcheck_pipeline.py` (with other imports):

```python
from factchecker.core.sources_config import EXTERNAL_SOURCES, get_searcher
```

---

## Skeleton Implementation Structure

This is a **skeleton** showing where logic will live; detailed internals (especially match detection and confidence math) will be filled in later.

```python
# At top of file (with other imports):
from factchecker.core.sources_config import EXTERNAL_SOURCES, get_searcher


class FactCheckPipeline(IPipeline):
    ...

    @log_stage("Claim Verification")
    async def _verify_claims(
        self, claims: List[ExtractedClaim]
    ) -> List[SearchResult]:
        """Verify each claim following Page-4 workflow.

        For each ExtractedClaim:
        1. Check if 'who' and 'what' answers are present
        2. If 'where' answer exists, reorder sources
        3. Search each source using 'who' and 'what' answers until match found
        4. Record confidence based on search results
        """
        all_search_results: List[SearchResult] = []

        # Get default source order (sorted by sequence number)
        source_order = sorted(
            EXTERNAL_SOURCES.keys(),
            key=lambda key: EXTERNAL_SOURCES[key].sequence,
        )

        for claim in claims:
            # Step 1: Check if both 'who' and 'what' answers present
            who_a = next(
                (q for q in claim.questions if q.question_type == "who"),
                None,
            )
            what_a = next(
                (q for q in claim.questions if q.question_type == "what"),
                None,
            )

            if not who_a or not what_a:
                self._record_no_confidence(claim)
                continue

            # Step 2: Get 'where' answer if present
            where_a = next(
                (q for q in claim.questions if q.question_type == "where"),
                None,
            )

            # Step 3: Determine source order (reorder if 'where' matches a source)
            claim_source_order = source_order.copy()
            if where_a:
                where_answer_lower = where_a.answer_text.lower()
                for platform in claim_source_order:
                    config = EXTERNAL_SOURCES[platform]
                    # Check if 'where' matches platform identifier or display name
                    if (
                        platform.lower() == where_answer_lower
                        or config.display_name.lower() == where_answer_lower
                    ):
                        # Move matching platform to first position
                        claim_source_order.remove(platform)
                        claim_source_order.insert(0, platform)
                        break

            # Step 4: Build search query and params
            search_query = f"{who_a.answer_text} {what_a.answer_text}"
            query_params = {
                "who": who_a.answer_text,
                "what": what_a.answer_text,
            }
            if where_a:
                query_params["where"] = where_a.answer_text

            # Step 5: Search each source until match found
            match_found = False
            claim_results: List[SearchResult] = []

            for platform in claim_source_order:
                try:
                    searcher = get_searcher(platform)
                    results = await searcher.search(search_query, query_params)
                    claim_results.extend(results)

                    # TODO: Implement actual match detection logic
                    # e.g., compare who_a / what_a against results
                    match_found = False  # placeholder

                    if match_found:
                        break  # Stop searching once match is found
                except Exception as exc:
                    logger.warning(
                        "Search failed for platform '%s': %s",
                        platform,
                        str(exc),
                        exc_info=True,
                    )
                    continue

            # Step 6: Record confidence
            self._record_confidence_from_match(
                claim, claim_results, match_found
            )

            # Collect all results
            all_search_results.extend(claim_results)

        return all_search_results

    # Helper methods (only 2 methods to be implemented later)

    def _record_no_confidence(self, claim: ExtractedClaim) -> None:
        """Record no confidence in claim and all questions.

        Page-4 branches:
        - Missing 'who' or 'what'
        - Exhausted all sources with no match
        """
        # TODO: Implement
        # Example behavior:
        #   claim.confidence = 0.0
        #   for q in claim.questions:
        #       q.confidence = 0.0
        #   claim.metadata["verification_status"] = "no_evidence"
        raise NotImplementedError

    def _record_confidence_from_match(
        self,
        claim: ExtractedClaim,
        search_results: List[SearchResult],
        match_found: bool,
    ) -> None:
        """Record confidence based on match results.

        If match_found:
          - Set 'who', 'what', 'where' question confidences to 1.0
          - Analyze search results for other questions ('when', 'how',
            'why', 'platform')
          - Update overall claim.confidence
        Else:
          - Delegate to _record_no_confidence(claim)
        """
        # TODO: Implement confidence recording logic
        raise NotImplementedError
```

---

## Implementation Notes

1. **SourceConfig Update Required (in `sources_config.py`)**
   - Add `sequence: int` field to `SourceConfig` model:
     ```python
     class SourceConfig(BaseModel):
         category: SourceCategory
         class_name: str
         display_name: str
         sequence: int  # Order number (lower = searched first)
     ```
   - Update `EXTERNAL_SOURCES` to include sequence values, for example:
     ```python
     EXTERNAL_SOURCES: dict[str, SourceConfig] = {
         "twitter": SourceConfig(
             category=SourceCategory.SOC,
             class_name="TwitterSearcher",
             display_name="Twitter",
             sequence=1,
         ),
         "bluesky": SourceConfig(
             category=SourceCategory.SOC,
             class_name="BlueSkySearcher",
             display_name="BlueSky",
             sequence=2,
         ),
         "news": SourceConfig(
             category=SourceCategory.NWS,
             class_name="NewsSearcher",
             display_name="News",
             sequence=3,
         ),
         "gov": SourceConfig(
             category=SourceCategory.GOV,
             class_name="GovernmentSearcher",
             display_name="Government",
             sequence=4,
         ),
     }
     ```
   - The exact numeric values are configurable; the plan just requires that **lower numbers mean earlier in the search order**.

2. **Source Reordering (Page-4 “where” behavior)**
   - When a `where` answer exists, we:
     - Match `where_a.answer_text` against:
       - Platform identifiers: `"twitter"`, `"bluesky"`, `"news"`, `"gov"`
       - Display names: `"Twitter"`, `"BlueSky"`, `"News"`, `"Government"`, etc.
     - Case-insensitive comparison is recommended.
     - If a match is found, that platform is moved to the front of `claim_source_order`.

3. **Search Query Building**
   - Initial simple approach:
     - Concatenate `who` and `what` answers into one query string.
   - Future refinements:
     - Normalize whitespace and punctuation
     - Limit length
     - Pass structured filters via `query_params`

4. **Match Detection (Future Work)**
   - Kept as a TODO in the skeleton to be implemented later.
   - Possible strategies:
     - Text similarity scoring between `what_a.answer_text` and `SearchResult.content`
     - Author/name matching between `who_a.answer_text` and `SearchResult.author`
     - Domain/URL heuristics
     - LLM-based classification scoring

5. **Confidence Recording**
   - `_record_no_confidence` represents “no evidence / no match”.
   - `_record_confidence_from_match` will:
     - Boost confidences on matching components (`who`, `what`, `where`)
     - Derive overall `claim.confidence` from individual components.

6. **Error Handling**
   - Each external search call is wrapped in a `try/except`:
     - On failure, log a warning and continue to the next platform.
   - The pipeline should still progress even if one source fails.

7. **Return Value**
   - `_verify_claims()` returns a flat `List[SearchResult]`:
     - Aggregation of `claim_results` for all claims.
     - Ordering is roughly by claim, then by source search order.

---

## Testing Considerations (for later implementation)

- Claims with valid `who` and `what` answers → ensure we enter the search path.
- Claims missing `who` or `what` → `_record_no_confidence` is invoked; no searches.
- Claims with and without `where` answers:
  - Confirm default sequence-based order when `where` is absent.
  - Confirm reordering works when `where` names a specific source.
- Verify:
  - Correct construction of `search_query` and `query_params`.
  - Correct early-exit behavior when `match_found` (once implemented).
  - That helper methods are called with expected parameters.
- Resilience:
  - Simulate searcher failures and ensure we continue to other sources.

---

## Next Steps

1. **Update `sources_config.py`**: Add `sequence: int` to `SourceConfig` and populate `EXTERNAL_SOURCES` with numeric sequences.
2. **Implement skeleton `_verify_claims()`** as outlined (inline logic + two helpers with `NotImplementedError`).
3. **Fill in `_record_no_confidence` and `_record_confidence_from_match`** with concrete logic.
4. **Add match detection implementation** inside the search loop.
5. **Write tests** for the pipeline behavior under different combinations of `who` / `what` / `where` answers and source availability.

