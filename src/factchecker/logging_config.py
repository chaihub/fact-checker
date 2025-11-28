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


def setup_logging(level=logging.INFO) -> logging.Logger:
    """Initialize logging with structured format."""
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(request_id)s | %(message)s"
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger("factchecker")
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


def get_logger(name: str) -> logging.LoggerAdapter:
    """Get logger with automatic request_id injection."""
    logger = logging.getLogger(f"factchecker.{name}")
    return logging.LoggerAdapter(logger, {"request_id": lambda: request_id_var.get()})


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
                    f"Stage '{stage_name}' completed",
                    extra={"elapsed_ms": f"{elapsed_ms:.2f}ms"},
                )
                return result
            except Exception as e:
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(
                    f"Stage '{stage_name}' failed: {str(e)}",
                    extra={"elapsed_ms": f"{elapsed_ms:.2f}ms"},
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
                    f"Stage '{stage_name}' completed",
                    extra={"elapsed_ms": f"{elapsed_ms:.2f}ms"},
                )
                return result
            except Exception as e:
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(
                    f"Stage '{stage_name}' failed: {str(e)}",
                    extra={"elapsed_ms": f"{elapsed_ms:.2f}ms"},
                    exc_info=True,
                )
                raise

        return (
            async_wrapper
            if asyncio.iscoroutinefunction(func)
            else sync_wrapper
        )

    return decorator
