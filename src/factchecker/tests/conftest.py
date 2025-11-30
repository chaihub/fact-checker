"""Pytest configuration and fixtures for FactChecker tests."""

import pytest
import logging
from factchecker.logging_config import RequestIdFilter, request_id_var


def pytest_configure(config):
    """Configure pytest with custom logging."""
    # Create a formatter that includes request_id
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(request_id)s %(name)s %(message)s"
    )
    
    # Get the logging handler that pytest creates
    # We need to update all handlers to include the filter
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)
        if not any(isinstance(f, RequestIdFilter) for f in handler.filters):
            handler.addFilter(RequestIdFilter())


@pytest.fixture(autouse=True)
def setup_logging_for_tests(caplog):
    """Configure logging for tests to capture request_id."""
    # Ensure caplog has the request_id filter
    caplog.handler.addFilter(RequestIdFilter())
    
    # Set the caplog formatter to include request_id and timestamp
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(request_id)s %(name)s %(message)s"
    )
    caplog.handler.setFormatter(formatter)
    
    # Set caplog to capture all logging
    caplog.set_level(logging.DEBUG)
    
    # Reset request_id to default before each test
    request_id_var.set("N/A")
    
    yield caplog
