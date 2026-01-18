"""External sources registry and configuration."""

from enum import Enum
from importlib import import_module

from pydantic import BaseModel

from factchecker.core.interfaces import BaseSearcher, SourceNotFoundError


class SourceCategory(str, Enum):
    """Category codes for external sources."""

    SOC = "SOC"  # Social Media
    NWS = "NWS"  # News/Commercial Media
    GOV = "GOV"  # Government/Official
    OTH = "OTH"  # Other/Academic/Research


class SourceConfig(BaseModel):
    """Configuration for an external source."""

    category: SourceCategory
    class_name: str
    display_name: str
    sequence: int  # Lower values are checked earlier in the default order; negative values are skipped


EXTERNAL_SOURCES: dict[str, SourceConfig] = {
    "twitter": SourceConfig(
        category=SourceCategory.SOC,
        class_name="TwitterSearcher",
        display_name="Twitter",
        sequence=1,
    ),
    "bluesky": SourceConfig(
        category=SourceCategory.SOC,
        class_name="BlueSkySearcher",
        display_name="BlueSky",
        sequence=-2,
    ),
    "news": SourceConfig(
        category=SourceCategory.NWS,
        class_name="NewsSearcher",
        display_name="News",
        sequence=-3,
    ),
    "gov": SourceConfig(
        category=SourceCategory.GOV,
        class_name="GovernmentSearcher",
        display_name="Government",
        sequence=-4,
    ),
}


def get_searcher(platform: str) -> BaseSearcher:
    """Dynamically instantiate a searcher by platform identifier.

    Args:
        platform: Platform identifier (key in EXTERNAL_SOURCES)

    Returns:
        Instantiated searcher instance

    Raises:
        SourceNotFoundError: If platform not in registry or import fails
    """
    if platform not in EXTERNAL_SOURCES:
        raise SourceNotFoundError(f"Platform '{platform}' not found in registry")

    config = EXTERNAL_SOURCES[platform]

    try:
        # Import searcher module dynamically
        module = import_module("factchecker.searchers")
        searcher_class = getattr(module, config.class_name)
        return searcher_class()
    except (ImportError, AttributeError) as e:
        raise SourceNotFoundError(
            f"Failed to instantiate {config.class_name} for platform '{platform}': {str(e)}"
        ) from e
