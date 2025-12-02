"""Centralized logging configuration for FactChecker."""

import logging
import asyncio
import contextvars
import traceback
from functools import wraps
from typing import Callable, Any
from datetime import datetime

# Context variable for request tracing
request_id_var: contextvars.ContextVar = contextvars.ContextVar(
    "request_id", default="N/A"
)

# Context variable for error tracking
error_context_var: contextvars.ContextVar = contextvars.ContextVar(
    "error_context", default=None
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


def _is_sensitive(key: str) -> bool:
    """Check if field name suggests sensitive data."""
    sensitive_keywords = ["password", "token", "secret", "image_data", "api_key"]
    return any(keyword in key.lower() for keyword in sensitive_keywords)


def _sanitize_value(value: Any) -> Any:
    """Sanitize value for logging (avoid image data, sensitive fields)."""
    if isinstance(value, bytes):
        return f"<bytes: {len(value)} bytes>"
    elif isinstance(value, dict):
        return {
            k: _sanitize_value(v)
            for k, v in value.items()
            if not _is_sensitive(k)
        }
    elif hasattr(value, "__dict__"):
        # For objects, show type and key fields
        return f"<{type(value).__name__}>"
    return str(value)


def _extract_params(args: tuple, kwargs: dict) -> dict:
    """
    Extract parameters from function call, excluding self and request objects.
    Sanitize to avoid logging sensitive data.
    """
    params = {}
    # Skip 'self' parameter for methods
    param_list = (
        list(args)[1:] if args and hasattr(args[0], "__dict__") else list(args)
    )

    for i, arg in enumerate(param_list):
        param_key = f"arg_{i}"
        params[param_key] = _sanitize_value(arg)

    for key, value in kwargs.items():
        params[key] = _sanitize_value(value)

    return params


def _extract_traceback_summary(exception: Exception) -> str:
    """Extract condensed traceback showing call chain."""
    tb_lines = traceback.format_exception(
        type(exception), exception, exception.__traceback__
    )
    # Return last 5 lines (most relevant)
    return "".join(tb_lines[-5:])


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
                # Import here to avoid circular imports
                from factchecker.pipeline.factcheck_pipeline import (
                    PipelineExecutionError,
                )

                # Wrap the exception with context
                wrapped_error = PipelineExecutionError(
                    message=str(e),
                    stage_name=stage_name,
                    function_name=func.__qualname__,
                    input_params=_extract_params(args, kwargs),
                    original_exception=e,
                )
                # Store error context
                error_context_var.set(
                    {
                        "stage": stage_name,
                        "function": func.__qualname__,
                        "error": wrapped_error,
                    }
                )
                raise wrapped_error

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
                # Import here to avoid circular imports
                from factchecker.pipeline.factcheck_pipeline import (
                    PipelineExecutionError,
                )

                # Wrap the exception with context
                wrapped_error = PipelineExecutionError(
                    message=str(e),
                    stage_name=stage_name,
                    function_name=func.__qualname__,
                    input_params=_extract_params(args, kwargs),
                    original_exception=e,
                )
                # Store error context
                error_context_var.set(
                    {
                        "stage": stage_name,
                        "function": func.__qualname__,
                        "error": wrapped_error,
                    }
                )
                raise wrapped_error

        return (
            async_wrapper
            if asyncio.iscoroutinefunction(func)
            else sync_wrapper
        )

    return decorator
