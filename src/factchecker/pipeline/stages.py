"""Pipeline stage definitions."""

from typing import List
from factchecker.core.models import ExtractedClaim, SearchResult


class PipelineStage:
    """Base class for pipeline stages."""

    pass


class CacheLookupStage(PipelineStage):
    """Stage for checking cache."""

    # TODO: Implement cache lookup logic
    pass


class ClaimExtractionStage(PipelineStage):
    """Stage for extracting claims from input."""

    # TODO: Implement claim extraction logic
    pass


class SearchParameterBuildingStage(PipelineStage):
    """Stage for building search parameters."""

    # TODO: Implement parameter building logic
    pass


class ExternalSearchStage(PipelineStage):
    """Stage for querying external sources."""

    # TODO: Implement external search coordination
    pass


class ResultProcessingStage(PipelineStage):
    """Stage for analyzing results and generating verdict."""

    # TODO: Implement result processing logic
    pass


class ResponseGenerationStage(PipelineStage):
    """Stage for formatting final response."""

    # TODO: Implement response generation logic
    pass


class CacheStorageStage(PipelineStage):
    """Stage for storing response in cache."""

    # TODO: Implement cache storage logic
    pass
