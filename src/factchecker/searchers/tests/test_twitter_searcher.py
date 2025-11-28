"""Tests for TwitterSearcher."""

import pytest
from unittest.mock import AsyncMock, patch
from factchecker.searchers.twitter_searcher import TwitterSearcher
from factchecker.core.models import SearchResult


@pytest.fixture
def searcher():
    return TwitterSearcher(api_key="test_key")


@pytest.mark.asyncio
async def test_twitter_search_initialization(searcher):
    """Test Twitter searcher initialization."""
    assert searcher.platform_name == "twitter"
    assert searcher.api_key == "test_key"


@pytest.mark.asyncio
async def test_twitter_search_returns_list(searcher):
    """Test that search returns a list."""
    results = await searcher.search("test claim", {})
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_twitter_search_with_params(searcher):
    """Test Twitter search with query parameters."""
    query_params = {"max_results": 10, "lang": "en"}
    results = await searcher.search("test claim", query_params)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_twitter_search_platform_name(searcher):
    """Test platform name property."""
    assert searcher.platform_name == "twitter"
