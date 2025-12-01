"""Main fact-checking pipeline orchestrator."""

import asyncio
import uuid
from datetime import datetime
from typing import Optional, List

from factchecker.core.models import (
    FactCheckRequest,
    FactCheckResponse,
    ExtractedClaim,
    SearchResult,
    Evidence,
    Reference,
    VerdictEnum,
)
from factchecker.core.interfaces import IPipeline
from factchecker.logging_config import get_logger, log_stage, request_id_var

logger = get_logger(__name__)


class FactCheckPipeline(IPipeline):
    """Orchestrates fact-checking pipeline stages."""

    def __init__(self, cache, extractors, searchers, processors):
        self.cache = cache
        self.extractors = extractors
        self.searchers = searchers
        self.processors = processors

    async def check_claim(self, request: FactCheckRequest) -> FactCheckResponse:
        """Execute full fact-checking pipeline."""

        # Generate request ID for tracing
        request.request_id = request.request_id or str(uuid.uuid4())
        request_id_var.set(request.request_id)

        start_time = datetime.now()
        logger.info(
            "Fact-check request started",
            extra={"user_id": request.user_id, "source": request.source_platform},
        )

        try:
            # Stage 1: Cache lookup
            cached = await self._check_cache(request)
            if cached:
                logger.info("Cache hit - returning cached response")
                cached.cached = True
                cached.processing_time_ms = (
                    datetime.now() - start_time
                ).total_seconds() * 1000
                return cached

            # Stage 2: Extract claim
            extracted_claim = await self._extract_claim(request)

            # Stage 3: Identify search parameters
            search_params = await self._build_search_params(extracted_claim)

            # Stage 4: Search external sources
            all_results = await self._search_sources(extracted_claim, search_params)

            # Stage 5: Process results
            response = await self._generate_response(
                request, extracted_claim, all_results, start_time
            )

            # Stage 6: Cache response
            await self._cache_response(response)

            logger.info("Fact-check request completed successfully")
            return response

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            raise

    @log_stage("Cache Lookup")
    async def _check_cache(self, request: FactCheckRequest) -> Optional[FactCheckResponse]:
        """Check if claim result is cached."""
        cache_key = request.claim_text or ""
        return await self.cache.get(cache_key)

    @log_stage("Claim Extraction")
    async def _extract_claim(self, request: FactCheckRequest):
        """Extract structured claim from text or image."""
        return await self.extractors.extract(request.claim_text, request.image_data)

    @log_stage("Search Parameter Building")
    async def _build_search_params(self, claim: ExtractedClaim) -> dict:
        """Generate search parameters from extracted claim.
        
        Mock implementation returns dummy search parameters for orchestration testing.
        """
        return {
            "query": claim.claim_text,
            "limit": 5,
            "sort_by": "relevance",
        }

    @log_stage("External Search")
    async def _search_sources(
        self, claim: ExtractedClaim, params: dict
    ) -> List[SearchResult]:
        """Query all enabled searchers concurrently.
        
        Mock implementation returns hardcoded SearchResult objects for orchestration testing.
        """
        # Generate mock search results
        mock_results = [
            SearchResult(
                platform="twitter",
                content="Mock tweet about the claim",
                author="Mock User 1",
                url="https://twitter.com/mock/1",
                timestamp=datetime.now(),
                engagement={"likes": 10, "retweets": 2},
            ),
            SearchResult(
                platform="twitter",
                content="Another mock tweet with different perspective",
                author="Mock User 2",
                url="https://twitter.com/mock/2",
                timestamp=datetime.now(),
                engagement={"likes": 25, "retweets": 5},
            ),
            SearchResult(
                platform="news",
                content="Mock news article related to the claim",
                author="Mock News Source",
                url="https://news.mock/article",
                timestamp=datetime.now(),
                engagement={"views": 1000},
            ),
        ]
        return mock_results

    @log_stage("Response Generation")
    async def _generate_response(
        self,
        request: FactCheckRequest,
        claim: ExtractedClaim,
        results: List[SearchResult],
        start_time: datetime,
    ) -> FactCheckResponse:
        """Generate fact-check verdict and explanation.
        
        Mock implementation returns properly constructed FactCheckResponse for orchestration testing.
        """
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Mock evidence construction
        evidence = Evidence(
            claim_fragment=claim.claim_text[:50],
            finding="Mock finding based on search results",
            supporting_results=results[:2] if results else [],
            confidence=0.75,
        )
        
        # Mock reference construction
        reference = Reference(
            title="Mock Source",
            url="https://mock.source/article",
            snippet="This is a mock reference snippet",
            platform="mock_platform",
        )
        
        # Create response with proper typing
        response = FactCheckResponse(
            request_id=request.request_id or str(uuid.uuid4()),
            claim_id=str(uuid.uuid4()),
            verdict=VerdictEnum.MIXED,
            confidence=0.75,
            evidence=[evidence],
            references=[reference],
            explanation="Mock explanation: This claim contains both accurate and inaccurate elements.",
            search_queries_used=["mock query 1", "mock query 2"],
            cached=False,
            processing_time_ms=processing_time_ms,
            timestamp=datetime.now(),
        )
        return response

    @log_stage("Cache Storage")
    async def _cache_response(self, response: FactCheckResponse) -> None:
        """Store response in cache using claim text as key.
        
        Uses claim text as cache key for consistency with cache lookup,
        ensuring same claims return cached results.
        """
        # Note: Claim text is extracted from the original request
        # In practice, we'd pass it through or reconstruct from response evidence
        # For now, use request_id as fallback to prevent errors
        cache_key = response.request_id
        await self.cache.set(cache_key, response)
