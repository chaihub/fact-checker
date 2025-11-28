"""Main fact-checking pipeline orchestrator."""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from factchecker.core.models import FactCheckRequest, FactCheckResponse
from factchecker.logging_config import get_logger, log_stage, request_id_var

logger = get_logger(__name__)


class FactCheckPipeline:
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
        return await self.cache.get(request.claim_text or "")

    @log_stage("Claim Extraction")
    async def _extract_claim(self, request: FactCheckRequest):
        """Extract structured claim from text or image."""
        return await self.extractors.extract(request.claim_text, request.image_data)

    @log_stage("Search Parameter Building")
    async def _build_search_params(self, claim):
        """Generate search parameters from extracted claim."""
        # TODO: Implement search parameter building
        return {}

    @log_stage("External Search")
    async def _search_sources(self, claim, params):
        """Query all enabled searchers concurrently."""
        # TODO: Implement concurrent searcher execution
        return []

    @log_stage("Response Generation")
    async def _generate_response(self, request, claim, results, start_time):
        """Generate fact-check verdict and explanation."""
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        # TODO: Implement response generation
        return None

    @log_stage("Cache Storage")
    async def _cache_response(self, response: FactCheckResponse):
        """Store response in cache."""
        await self.cache.set(response.request_id, response)
