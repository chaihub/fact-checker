"""Data models for FactChecker."""

from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, field_validator


class FactCheckRequest(BaseModel):
    """
    Claim input for fact-checking.
    At least one of claim_text or image_data must be present.
    """

    claim_text: Optional[str] = None
    image_data: Optional[bytes] = None
    user_id: str
    source_platform: str = "whatsapp"
    request_id: Optional[str] = None

    @field_validator("claim_text", "image_data", mode="before")
    @classmethod
    def at_least_one_required(cls, v, info):
        """Validate that at least one input is provided."""
        if not info.data.get("claim_text") and not info.data.get("image_data"):
            raise ValueError(
                "At least one of claim_text or image_data must be provided"
            )
        return v

    class Config:
        str_strip_whitespace = True


class ExtractedClaim(BaseModel):
    """Output from extractors (Image or Text)."""

    claim_text: str
    extracted_from: Literal["image", "text", "hybrid"]
    confidence: float
    raw_input_type: Literal["text_only", "image_only", "both"]
    metadata: dict = {}


class SearchResult(BaseModel):
    """Individual result from a searcher."""

    platform: str
    content: str
    author: str
    url: str
    timestamp: datetime
    engagement: dict = {}
    metadata: dict = {}


class VerdictEnum(str, Enum):
    """Possible fact-check verdicts."""

    AUTHENTIC = "authentic"
    NOT_AUTHENTIC = "not_authentic"
    MIXED = "mixed"
    UNCLEAR = "unclear"


class Reference(BaseModel):
    """Reference source for fact-check."""

    title: str
    url: str
    snippet: str
    platform: str


class Evidence(BaseModel):
    """Supporting evidence for verdict."""

    claim_fragment: str
    finding: str
    supporting_results: List[SearchResult]
    confidence: float


class FactCheckResponse(BaseModel):
    """Complete fact-check output."""

    request_id: str
    claim_id: str
    verdict: VerdictEnum
    confidence: float
    evidence: List[Evidence]
    references: List[Reference]
    explanation: str
    search_queries_used: List[str]
    cached: bool
    processing_time_ms: float
    timestamp: datetime
