"""Searchers for external sources (Twitter, BlueSky, etc.)."""

from factchecker.searchers.twitter_searcher import TwitterSearcher
from factchecker.searchers.bluesky_searcher import BlueSkySearcher
from factchecker.searchers.news_searcher import NewsSearcher
from factchecker.searchers.government_searcher import GovernmentSearcher

__all__ = [
    "TwitterSearcher",
    "BlueSkySearcher",
    "NewsSearcher",
    "GovernmentSearcher",
]
