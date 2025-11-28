"""Tests for BlueSkySearcher."""

import pytest
from factchecker.searchers.bluesky_searcher import BlueSkySearcher


@pytest.fixture
def searcher():
    return BlueSkySearcher(handle="test_handle", password="test_password")


@pytest.mark.asyncio
async def test_bluesky_search_initialization(searcher):
    """Test BlueSky searcher initialization."""
    assert searcher.platform_name == "bluesky"
    assert searcher.handle == "test_handle"


@pytest.mark.asyncio
async def test_bluesky_search_returns_list(searcher):
    """Test that search returns a list."""
    results = await searcher.search("test claim", {})
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_bluesky_search_platform_name(searcher):
    """Test platform name property."""
    assert searcher.platform_name == "bluesky"
