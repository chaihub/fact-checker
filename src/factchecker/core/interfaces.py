"""Abstract base interfaces for FactChecker components."""

from abc import ABC, abstractmethod
from typing import List, Optional
from .models import ExtractedClaim, SearchResult, FactCheckResponse


class SourceNotFoundError(Exception):
    """Raised when a requested external source is not found."""

    pass


class BaseExtractor(ABC):
    """Abstract base for text and image extractors."""

    @abstractmethod
    async def extract(
        self, claim_text: Optional[str], image_data: Optional[bytes]
    ) -> ExtractedClaim:
        """Extract structured claim from input."""
        pass


class BaseSearcher(ABC):
    """Abstract base for all searchers (Twitter, BlueSky, etc.)."""

    @abstractmethod
    async def search(self, claim: str, query_params: dict) -> List[SearchResult]:
        """Search external source for results."""
        pass

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Identifier for this searcher."""
        pass


class BaseProcessor(ABC):
    """Abstract base for result processors."""

    @abstractmethod
    async def process(self, claim: ExtractedClaim, results: List[SearchResult]) -> dict:
        """Analyze results and generate verdict."""
        pass


class IPipeline(ABC):
    """Fact-checker pipeline interface."""

    @abstractmethod
    async def check_claim(self, request) -> FactCheckResponse:
        """Execute full fact-checking pipeline."""
        pass
