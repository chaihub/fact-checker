"""Main fact-checking pipeline orchestrator."""

import asyncio
import uuid
import traceback
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
    ErrorDetails,
)
from factchecker.core.interfaces import IPipeline
from factchecker.extractors.text_extractor import TextExtractor
from factchecker.extractors.image_extractor import ImageExtractor
from factchecker.extractors.image_handler import ImageHandler
from factchecker.extractors.text_image_extractor import TextImageExtractor
from factchecker.logging_config import (
    get_logger,
    log_stage,
    request_id_var,
    error_context_var,
)

logger = get_logger(__name__)


class PipelineExecutionError(Exception):
    """Exception with pipeline execution context."""

    def __init__(
        self,
        message: str,
        stage_name: str,
        function_name: str,
        input_params: dict,
        original_exception: Exception,
    ):
        self.message = message
        self.stage_name = stage_name
        self.function_name = function_name
        self.input_params = input_params
        self.original_exception = original_exception
        super().__init__(message)


class FactCheckPipeline(IPipeline):
    """Orchestrates fact-checking pipeline stages."""

    def __init__(self, cache, extractors, searchers, processors):
        self.cache = cache
        self.searchers = searchers
        self.processors = processors
        # Extractors dict should contain "text", "image", "image_handler", and "text_image_extractor"
        self.text_extractor: TextExtractor = extractors.get("text")
        self.image_extractor: ImageExtractor = extractors.get("image")
        self.image_handler: ImageHandler = extractors.get("image_handler", ImageHandler())
        self.text_image_extractor: TextImageExtractor = extractors.get(
            "text_image_extractor", TextImageExtractor()
        )

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

            # Stage 2: Extract claims
            extracted_claims = await self._extract_claims(request)

            # Stage 3: Search external sources
            all_results = await self._verify_claims(extracted_claims)

            # Stage 4: Process results
            response = await self._generate_response(
                request, extracted_claims, all_results, start_time
            )

            # Stage 5: Cache response
            await self._cache_response(response)

            logger.info("Fact-check request completed successfully")
            return response

        except PipelineExecutionError as e:
            logger.error(
                f"Pipeline failed at stage '{e.stage_name}': {str(e)}", exc_info=True
            )
            error_response = await self._generate_error_response(
                request, e, start_time
            )
            logger.info("Fact-check request completed with error response")
            return error_response
        except Exception as e:
            logger.error(
                f"Pipeline encountered unexpected error: {str(e)}", exc_info=True
            )
            error_response = await self._generate_error_response(
                request, e, start_time
            )
            logger.info("Fact-check request completed with error response")
            return error_response

    @log_stage("Cache Lookup")
    async def _check_cache(self, request: FactCheckRequest) -> Optional[FactCheckResponse]:
        """Check if claim result is cached."""
        cache_key = request.claim_text or ""
        return await self.cache.get(cache_key)

    @log_stage("Claim Extraction")
    async def _extract_claims(self, request: FactCheckRequest) -> List[ExtractedClaim]:
        """Extract structured claim from text and/or image following Page-3 workflow.
        
        Workflow:
        1. If text exists → Extract text claim
        2. If image exists → Check if text image
        3. If text image → Check if nested
        4. Extract claims from respective image texts
        5. Return all extracted claims in the order: main, quoted, quoted-within-quoted (Note: only the main claim is mandatory, the rest are optional)
        """
        claims: List[ExtractedClaim] = []
        
        # Step 1: Extract text claim if text input exists
        if request.claim_text:
            text_claim = await self._extract_text_claim(request.claim_text)
            if text_claim:
                claims.append(text_claim)
        
        # Step 2: Process image if present
        if request.image_data:
            image_claims = await self._process_image_input(request.image_data)
            claims.extend(image_claims)
        
        # Step 3: Return text claim if available, otherwise return first image claim
        if claims:
            return claims
        else:
            # Error case: no claims extracted
            return self._create_error_claim("No claims extracted from input")
    
    async def _extract_text_claim(self, claim_text: str) -> Optional[ExtractedClaim]:
        """Extract claim from text input."""
        try:
            return await self.text_extractor.extract(claim_text, None)
        except Exception as e:
            logger.warning(f"TextExtractor failed: {str(e)}", exc_info=True)
            return None
    
    async def _process_image_input(
        self, image_data: bytes
    ) -> List[ExtractedClaim]:
        """Process image input following workflow decisions.
        
        Returns list of ExtractedClaim objects from image processing.
        """
        claims: List[ExtractedClaim] = []
        
        try:
            # Check if this is a text image
            is_text_image = await self.image_handler.detect_text_image(image_data)
            
            if not is_text_image:
                # Not a text image - return error as no text detected
                error_claim = self._create_error_claim(
                    "Image does not contain readable text"
                )
                claims.append(error_claim)
                return claims
            
            # It's a text image - check for nesting
            has_nested_image = await self.image_handler.detect_nested_image(image_data)
            
            if has_nested_image:
                # Nested image case: separate and extract from both
                # TODO: Need to decide the strategy to handle this
                top_image, inside_image = (
                    await self.image_handler.separate_nested_image(image_data)
                )
                
                # Extract from top image
                top_claim = await self.text_image_extractor.extract_from_top_image(
                    top_image
                )
                if top_claim:
                    claims.append(top_claim)  # Output C
                
                # Extract from inside image
                inside_claim = (
                    await self.text_image_extractor.extract_from_inside_image(
                        inside_image
                    )
                )
                if inside_claim:
                    claims.append(inside_claim)  # Output D
            else:
                # Simple text image: extract directly
                image_claim = await self.text_image_extractor.extract_from_text_image(
                    image_data
                )
                if image_claim:
                    claims.append(image_claim)  # Output B
        except Exception as e:
            logger.warning(
                f"Image processing failed: {str(e)}", exc_info=True
            )
        
        return claims
    
    def _create_error_claim(self, error_message: str) -> ExtractedClaim:
        """Create an error ExtractedClaim when extraction fails."""
        return ExtractedClaim(
            claim_text="",
            extracted_from="hybrid",
            confidence=0.0,
            raw_input_type="both",
            metadata={"error": error_message},
            questions=[],
        )

    @log_stage("External Search")
    async def _verify_claims(
        self, claims: List[ExtractedClaim]
    ) -> List[SearchResult]:
        """Query all enabled searchers concurrently.
        
        Mock implementation returns hardcoded SearchResult objects for orchestration testing.
        """
        # Generate mock search results
        mock_results = [
            SearchResult(
                external_source="twitter",
                content="Mock tweet about the claim",
                author="Mock User 1",
                url="https://twitter.com/mock/1",
                timestamp=datetime.now(),
                engagement={"likes": 10, "retweets": 2},
            ),
            SearchResult(
                external_source="twitter",
                content="Another mock tweet with different perspective",
                author="Mock User 2",
                url="https://twitter.com/mock/2",
                timestamp=datetime.now(),
                engagement={"likes": 25, "retweets": 5},
            ),
            SearchResult(
                external_source="news",
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
            external_source="news",
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

    async def _generate_error_response(
        self,
        request: FactCheckRequest,
        exception: Exception,
        start_time: datetime,
    ) -> FactCheckResponse:
        """Generate error response with detailed debugging information."""
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Extract error context
        if isinstance(exception, PipelineExecutionError):
            failed_stage = exception.stage_name
            failed_function = exception.function_name
            error_type = type(exception.original_exception).__name__
            error_message = str(exception.original_exception)
            input_parameters = exception.input_params
            traceback_summary = self._extract_traceback_summary(
                exception.original_exception
            )
        else:
            # Fallback for unexpected exceptions
            failed_stage = "Unknown"
            failed_function = "Unknown"
            error_type = type(exception).__name__
            error_message = str(exception)
            input_parameters = {}
            traceback_summary = self._extract_traceback_summary(exception)

        # Create ErrorDetails object
        error_details = ErrorDetails(
            failed_stage=failed_stage,
            failed_function=failed_function,
            error_type=error_type,
            error_message=error_message,
            input_parameters=input_parameters,
            traceback_summary=traceback_summary,
            timestamp=datetime.now(),
        )

        # Create error response
        response = FactCheckResponse(
            request_id=request.request_id or str(uuid.uuid4()),
            claim_id=str(uuid.uuid4()),
            verdict=VerdictEnum.ERROR,
            confidence=0.0,
            evidence=None,
            references=None,
            explanation=f"Fact-check failed at stage: {error_details.failed_stage}. {error_details.error_message}",
            search_queries_used=None,
            cached=False,
            processing_time_ms=processing_time_ms,
            timestamp=datetime.now(),
            error_details=error_details,
        )
        return response

    def _extract_traceback_summary(self, exception: Exception) -> str:
        """Extract condensed traceback showing call chain."""
        tb_lines = traceback.format_exception(
            type(exception), exception, exception.__traceback__
        )
        # Return last 5 lines (most relevant)
        return "".join(tb_lines[-5:])
