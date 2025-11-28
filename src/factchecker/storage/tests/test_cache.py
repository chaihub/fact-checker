"""Tests for Cache."""

import pytest
from datetime import datetime, timedelta
from factchecker.storage.cache import Cache
from factchecker.core.models import FactCheckResponse, VerdictEnum


@pytest.fixture
def cache():
    return Cache(ttl_seconds=3600)


@pytest.fixture
def sample_response():
    return FactCheckResponse(
        request_id="test-123",
        claim_id="claim-123",
        verdict=VerdictEnum.AUTHENTIC,
        confidence=0.95,
        evidence=[],
        references=[],
        explanation="Test explanation",
        search_queries_used=["query1"],
        cached=False,
        processing_time_ms=100.5,
        timestamp=datetime.now(),
    )


@pytest.mark.asyncio
async def test_cache_set_and_get(cache, sample_response):
    """Test setting and getting from cache."""
    await cache.set("test-key", sample_response)
    result = await cache.get("test-key")
    assert result is not None
    assert result.request_id == sample_response.request_id


@pytest.mark.asyncio
async def test_cache_miss(cache):
    """Test cache miss for non-existent key."""
    result = await cache.get("nonexistent-key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_clear(cache, sample_response):
    """Test clearing cache."""
    await cache.set("key1", sample_response)
    await cache.set("key2", sample_response)
    assert cache.size() == 2
    await cache.clear()
    assert cache.size() == 0


@pytest.mark.asyncio
async def test_cache_ttl_expiration():
    """Test that items expire after TTL."""
    cache = Cache(ttl_seconds=1)
    response = FactCheckResponse(
        request_id="test-123",
        claim_id="claim-123",
        verdict=VerdictEnum.AUTHENTIC,
        confidence=0.95,
        evidence=[],
        references=[],
        explanation="Test",
        search_queries_used=[],
        cached=False,
        processing_time_ms=100.0,
        timestamp=datetime.now(),
    )
    await cache.set("expiring-key", response)

    # Item should exist initially
    assert await cache.get("expiring-key") is not None

    # Manually expire by modifying cache internals (for testing)
    cache._cache["expiring-key"]["expires_at"] = datetime.now() - timedelta(
        seconds=1
    )

    # Item should be expired now
    assert await cache.get("expiring-key") is None
