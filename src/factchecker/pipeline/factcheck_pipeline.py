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
    ClaimQuestion,
)
from factchecker.core.interfaces import IPipeline
from factchecker.core.sources_config import EXTERNAL_SOURCES, get_searcher
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

        # Step 0: Determine default source order from configured sequence numbers
        source_order = sorted(
            EXTERNAL_SOURCES.keys(),
            key=lambda key: EXTERNAL_SOURCES[key].sequence,
        )

        for claim in claims:
            # Step 1: Check if both 'who' and 'what' answers are present
            who_a: Optional[ClaimQuestion] = next(
                (q for q in claim.questions if q.question_type == "who"),
                None,
            )
            what_a: Optional[ClaimQuestion] = next(
                (q for q in claim.questions if q.question_type == "what"),
                None,
            )

            if not who_a or not what_a:
                # No structured who/what → cannot verify; record no confidence
                self._record_no_confidence(claim)
                continue

            # Step 2: Get 'where' answer if present
            where_a: Optional[ClaimQuestion] = next(
                (q for q in claim.questions if q.question_type == "where"),
                None,
            )

            # Step 3: Determine source order (reorder if 'where' matches a source)
            claim_source_order = list(source_order)
            if where_a and where_a.answer_text:
                where_answer_lower = where_a.answer_text.lower()
                for platform in list(claim_source_order):
                    config = EXTERNAL_SOURCES[platform]
                    if platform.lower() == where_answer_lower:
                        claim_source_order.remove(platform)
                        claim_source_order.insert(0, platform)
                        break

            # Step 4: Build search query and params
            # TODO: Revisit if search query is to be formed here or within the search function
            search_query = f"{who_a.answer_text} {what_a.answer_text}"
            query_params: dict[str, str] = {
                "who": who_a.answer_text,
                "what": what_a.answer_text,
            }
            if where_a and where_a.answer_text:
                query_params["where"] = where_a.answer_text

            # Step 5: Search each source until match found (match logic TBD)
            match_found = False
            claim_results: List[SearchResult] = []

            for platform in claim_source_order:
                try:
                    searcher = get_searcher(platform)
                    results = await searcher.search(search_query, query_params)
                    claim_results.extend(results)

                    # TODO: Implement real match-detection logic
                    # For now, keep match_found as False so confidence logic
                    # will treat this as "no decisive match".
                    match_found = False

                    if match_found:
                        break
                except Exception as exc:
                    logger.warning(
                        "Search failed for platform '%s': %s",
                        platform,
                        str(exc),
                        exc_info=True,
                    )
                    continue

            # Step 6: Record confidence based on whether a match was found
            self._record_confidence_from_match(claim, claim_results, match_found)

            # Collect all results
            all_search_results.extend(claim_results)

        return all_search_results

    def _record_no_confidence(self, claim: ExtractedClaim) -> None:
        """Record no confidence in the claim and all its component questions.

        Used when the pipeline cannot verify the claim (e.g., missing who/what
        or no decisive match in any external source).
        """
        claim.confidence = 0.0
        #for question in claim.questions:
        #    question.confidence = 0.0

        metadata = dict(claim.metadata) if claim.metadata is not None else {}
        metadata["verification_status"] = "no_evidence"
        claim.metadata = metadata

    def _record_confidence_from_match(
        self,
        claim: ExtractedClaim,
        search_results: List[SearchResult],
        match_found: bool,
    ) -> None:
        """Record confidence values on the claim based on search results.

        TODO: This is a first-pass implementation; detailed scoring will be refined
        later. For now:

        - If no match was found (or there are no results), treat as no evidence.
        - If a match was found, boost confidence on who/what/where components,
          and assign moderate confidence to other components.
        """
        if not match_found or not search_results:
            self._record_no_confidence(claim)
            return

        # TODO: Check if boosting is needed
        # Boost key components when we believe a match exists.
        has_questions = bool(claim.questions)
        for question in claim.questions:
            if question.question_type in ("who", "what", "where"):
                question.confidence = 1.0
            else:
                # Non-core components get a moderate default; this will be
                # replaced later with result-driven scoring.
                if question.confidence < 0.5:
                    question.confidence = 0.5

        if has_questions:
            claim.confidence = sum(
                q.confidence for q in claim.questions
            ) / len(claim.questions)
        else:
            # Fallback if no structured questions exist
            claim.confidence = 1.0

        metadata = dict(claim.metadata) if claim.metadata is not None else {}
        metadata["verification_status"] = "matched"
        metadata["result_count"] = len(search_results)
        claim.metadata = metadata

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
