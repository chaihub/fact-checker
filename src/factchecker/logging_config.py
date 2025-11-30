"""Centralized logging configuration for FactChecker."""

import logging
import asyncio
import contextvars
from functools import wraps
from typing import Callable
from datetime import datetime

# Context variable for request tracing
request_id_var: contextvars.ContextVar = contextvars.ContextVar(
    "request_id", default="N/A"
)


class RequestIdFilter(logging.Filter):
    """Filter to inject request_id context variable into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to the log record."""
        record.request_id = request_id_var.get()
        return True


class RequestIdLoggerAdapter(logging.LoggerAdapter):
    """LoggerAdapter that injects request_id from context variable."""

    def process(self, msg, kwargs):
        """Process message to include request_id in the message itself."""
        request_id = request_id_var.get()
        # Add request_id to the LogRecord via extra dict
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"]["request_id"] = request_id
        return msg, kwargs


def setup_logging(level=logging.INFO) -> logging.Logger:
    """Initialize logging with structured format."""
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(request_id)s | %(message)s"
    )
    handler.setFormatter(formatter)

    # Add filter to inject request_id as fallback
    request_id_filter = RequestIdFilter()
    handler.addFilter(request_id_filter)

    logger = logging.getLogger("factchecker")
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


def get_logger(name: str) -> logging.LoggerAdapter:
    """Get logger with automatic request_id injection."""
    logger = logging.getLogger(f"factchecker.{name}")
    
    # Ensure the logger has the request_id filter
    if not any(isinstance(f, RequestIdFilter) for f in logger.filters):
        logger.addFilter(RequestIdFilter())
    
    # Return a custom LoggerAdapter that injects request_id into extra dict
    return RequestIdLoggerAdapter(logger, {})


def log_stage(stage_name: str):
    """Decorator to log stage execution with timing."""

    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.info(f"Stage '{stage_name}' started")
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.info(
                    f"Stage '{stage_name}' completed (elapsed: {elapsed_ms:.2f}ms)"
                )
                return result
            except Exception as e:
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(
                    f"Stage '{stage_name}' failed: {str(e)} (elapsed: {elapsed_ms:.2f}ms)",
                    exc_info=True,
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.info(f"Stage '{stage_name}' started")
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.info(
                    f"Stage '{stage_name}' completed (elapsed: {elapsed_ms:.2f}ms)"
                )
                return result
            except Exception as e:
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(
                    f"Stage '{stage_name}' failed: {str(e)} (elapsed: {elapsed_ms:.2f}ms)",
                    exc_info=True,
                )
                raise

        return (
            async_wrapper
            if asyncio.iscoroutinefunction(func)
            else sync_wrapper
        )

    return decorator
