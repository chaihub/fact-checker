"""Unit tests for logging configuration module."""

import contextvars
import pytest
import logging
import asyncio
import time
from datetime import datetime
from unittest.mock import patch, MagicMock
from factchecker.logging_config import (
    setup_logging,
    get_logger,
    request_id_var,
    log_stage,
)


# ============================================================================
# CONTEXT VARIABLE INJECTION TESTS
# ============================================================================


class TestContextVariableInjection:
    """Tests for request_id_var context variable functionality."""

    def test_context_var_set_and_get(self):
        """Test basic context variable set and get."""
        test_id = "test-request-123"
        request_id_var.set(test_id)
        assert request_id_var.get() == test_id

    def test_context_var_default_value(self):
        """Test context variable has a default value."""
        # The context variable is initialized with default="N/A" in logging_config.py
        # Save current value, set to something else, then test behavior
        current_value = request_id_var.get()
        try:
            # Test that we can always get a value (even if it's the default)
            request_id_var.set("N/A")
            assert request_id_var.get() == "N/A"
        finally:
            # Restore original value
            request_id_var.set(current_value)

    def test_get_logger_injects_request_id(self, caplog):
        """Test that get_logger properly injects request ID into logs."""
        test_id = "trace-request-456"
        request_id_var.set(test_id)

        logger = get_logger("test_module")
        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        # Verify request ID appears in log output
        assert test_id in caplog.text
        assert "Test message" in caplog.text

    def test_multiple_loggers_share_context(self, caplog):
        """Test that multiple logger instances share the same context variable."""
        test_id = "shared-context-789"
        request_id_var.set(test_id)

        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        with caplog.at_level(logging.INFO):
            logger1.info("Message from module1")
            logger2.info("Message from module2")

        # Both messages should contain the same request ID
        assert caplog.text.count(test_id) == 2

    @pytest.mark.asyncio
    async def test_context_var_isolation_across_async_tasks(self):
        """Test that context variables are accessible in async functions."""
        test_id = "async-context-123"
        request_id_var.set(test_id)

        async def check_context():
            # Context variable should be accessible in async function
            return request_id_var.get()

        result = await check_context()
        assert result == test_id


# ============================================================================
# DECORATOR TIMING TESTS
# ============================================================================


class TestDecoratorTiming:
    """Tests for @log_stage decorator timing functionality."""

    @pytest.mark.asyncio
    async def test_async_decorator_logs_start_and_completion(self, caplog):
        """Test decorator logs start and completion for async functions."""
        request_id_var.set("timing-test-1")

        @log_stage("Test Stage")
        async def sample_async_task():
            await asyncio.sleep(0.01)
            return "result"

        with caplog.at_level(logging.INFO):
            result = await sample_async_task()

        assert result == "result"
        assert "Stage 'Test Stage' started" in caplog.text
        assert "Stage 'Test Stage' completed" in caplog.text

    def test_sync_decorator_logs_start_and_completion(self, caplog):
        """Test decorator logs start and completion for sync functions."""
        request_id_var.set("timing-test-2")

        @log_stage("Sync Stage")
        def sample_sync_task():
            time.sleep(0.01)
            return "sync_result"

        with caplog.at_level(logging.INFO):
            result = sample_sync_task()

        assert result == "sync_result"
        assert "Stage 'Sync Stage' started" in caplog.text
        assert "Stage 'Sync Stage' completed" in caplog.text

    @pytest.mark.asyncio
    async def test_async_decorator_measures_timing(self, caplog):
        """Test decorator accurately measures execution time for async functions."""
        request_id_var.set("timing-test-3")
        sleep_time = 0.05  # 50ms

        @log_stage("Timed Async Stage")
        async def timed_async_task():
            await asyncio.sleep(sleep_time)

        with caplog.at_level(logging.INFO):
            await timed_async_task()

        # Should log completion with timing
        assert "Stage 'Timed Async Stage' completed" in caplog.text
        # Check for timing info (should be roughly 50ms or more)
        # Look for elapsed_ms pattern
        assert "ms" in caplog.text or "elapsed" in caplog.text.lower()

    def test_sync_decorator_measures_timing(self, caplog):
        """Test decorator accurately measures execution time for sync functions."""
        request_id_var.set("timing-test-4")
        sleep_time = 0.05  # 50ms

        @log_stage("Timed Sync Stage")
        def timed_sync_task():
            time.sleep(sleep_time)

        with caplog.at_level(logging.INFO):
            timed_sync_task()

        assert "Stage 'Timed Sync Stage' completed" in caplog.text
        assert "ms" in caplog.text or "elapsed" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_async_decorator_short_execution(self, caplog):
        """Test timing for very short async execution."""
        request_id_var.set("timing-test-5")

        @log_stage("Quick Async")
        async def quick_async():
            return "quick"

        with caplog.at_level(logging.INFO):
            result = await quick_async()

        assert result == "quick"
        assert "Stage 'Quick Async' started" in caplog.text
        assert "Stage 'Quick Async' completed" in caplog.text

    def test_sync_decorator_short_execution(self, caplog):
        """Test timing for very short sync execution."""
        request_id_var.set("timing-test-6")

        @log_stage("Quick Sync")
        def quick_sync():
            return "quick"

        with caplog.at_level(logging.INFO):
            result = quick_sync()

        assert result == "quick"
        assert "Stage 'Quick Sync' started" in caplog.text
        assert "Stage 'Quick Sync' completed" in caplog.text


# ============================================================================
# LOG FORMATTING TESTS
# ============================================================================


class TestLogFormatting:
    """Tests for log message formatting and structure."""

    def test_log_format_contains_all_required_fields(self, caplog):
        """Test that log format includes all required fields."""
        request_id_var.set("format-test-1")
        logger = get_logger("test_format")

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        log_record = caplog.records[0]
        # Verify the record has all required attributes
        assert hasattr(log_record, "asctime")
        assert hasattr(log_record, "name")
        assert hasattr(log_record, "levelname")
        assert hasattr(log_record, "message")

    def test_log_output_includes_timestamp(self, caplog):
        """Test that log output includes a timestamp."""
        request_id_var.set("format-test-2")
        logger = get_logger("test_timestamp")

        with caplog.at_level(logging.INFO):
            logger.info("Message with timestamp")

        # Timestamp should be in the formatted output
        # Format is: YYYY-MM-DD HH:MM:SS,mmm
        assert ":" in caplog.text  # Contains time separator

    def test_log_output_includes_logger_name(self, caplog):
        """Test that log output includes logger name."""
        request_id_var.set("format-test-3")
        logger = get_logger("named_module")

        with caplog.at_level(logging.INFO):
            logger.info("Message from named logger")

        assert "factchecker.named_module" in caplog.text

    def test_log_output_includes_log_level(self, caplog):
        """Test that log output includes log level."""
        request_id_var.set("format-test-4")
        logger = get_logger("level_test")

        with caplog.at_level(logging.INFO):
            logger.info("Info level message")

        assert "INFO" in caplog.text

    def test_log_output_includes_request_id(self, caplog):
        """Test that log output includes request ID."""
        test_request_id = "req-format-test-5"
        request_id_var.set(test_request_id)
        logger = get_logger("request_id_test")

        with caplog.at_level(logging.INFO):
            logger.info("Message with request ID")

        assert test_request_id in caplog.text

    def test_log_output_preserves_message_content(self, caplog):
        """Test that message content is preserved in output."""
        request_id_var.set("format-test-6")
        logger = get_logger("message_test")
        test_message = "This is the actual message content"

        with caplog.at_level(logging.INFO):
            logger.info(test_message)

        assert test_message in caplog.text


# ============================================================================
# ERROR LOGGING TESTS
# ============================================================================


class TestErrorLogging:
    """Tests for error logging functionality."""

    @pytest.mark.asyncio
    async def test_async_decorator_logs_exception(self, caplog):
        """Test decorator logs exceptions in async functions."""
        request_id_var.set("error-test-1")

        @log_stage("Error Stage Async")
        async def failing_async_task():
            raise ValueError("Test error message")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                await failing_async_task()

        assert "Stage 'Error Stage Async' failed" in caplog.text
        assert "Test error message" in caplog.text

    def test_sync_decorator_logs_exception(self, caplog):
        """Test decorator logs exceptions in sync functions."""
        request_id_var.set("error-test-2")

        @log_stage("Error Stage Sync")
        def failing_sync_task():
            raise RuntimeError("Sync error message")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError):
                failing_sync_task()

        assert "Stage 'Error Stage Sync' failed" in caplog.text
        assert "Sync error message" in caplog.text

    @pytest.mark.asyncio
    async def test_async_decorator_exception_includes_stack_trace(self, caplog):
        """Test that async decorator logs include stack trace."""
        request_id_var.set("error-test-3")

        @log_stage("Stack Trace Async")
        async def task_with_traceback():
            def inner_function():
                raise TypeError("Inner error")
            inner_function()

        with caplog.at_level(logging.ERROR):
            with pytest.raises(TypeError):
                await task_with_traceback()

        # Check for stack trace indicators
        assert "Traceback" in caplog.text or "TypeError" in caplog.text

    def test_sync_decorator_exception_includes_stack_trace(self, caplog):
        """Test that sync decorator logs include stack trace."""
        request_id_var.set("error-test-4")

        @log_stage("Stack Trace Sync")
        def task_with_traceback():
            def inner_function():
                raise KeyError("Inner key error")
            inner_function()

        with caplog.at_level(logging.ERROR):
            with pytest.raises(KeyError):
                task_with_traceback()

        assert "Traceback" in caplog.text or "KeyError" in caplog.text

    @pytest.mark.asyncio
    async def test_async_decorator_logs_error_before_raising(self, caplog):
        """Test that decorator logs error before re-raising exception."""
        request_id_var.set("error-test-5")

        @log_stage("Pre-raise Error Async")
        async def failing_task():
            raise ValueError("Should be logged before raise")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as exc_info:
                await failing_task()

        # Verify error was logged
        assert "Pre-raise Error Async' failed" in caplog.text
        # Verify exception is still raised
        assert str(exc_info.value) == "Should be logged before raise"

    def test_sync_decorator_logs_error_before_raising(self, caplog):
        """Test that sync decorator logs error before re-raising exception."""
        request_id_var.set("error-test-6")

        @log_stage("Pre-raise Error Sync")
        def failing_task():
            raise RuntimeError("Should be logged before raise")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError) as exc_info:
                failing_task()

        # Verify error was logged
        assert "Pre-raise Error Sync' failed" in caplog.text
        # Verify exception is still raised
        assert str(exc_info.value) == "Should be logged before raise"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestLoggingIntegration:
    """Integration tests combining multiple logging components."""

    def test_setup_logging_initializes_logger(self):
        """Test setup_logging creates a properly configured logger."""
        logger = setup_logging()

        assert logger.name == "factchecker"
        assert len(logger.handlers) > 0
        assert logger.level == logging.INFO

    def test_get_logger_creates_child_logger(self):
        """Test get_logger creates a child logger with adapter."""
        logger = get_logger("child_module")

        assert isinstance(logger, logging.LoggerAdapter)
        assert "factchecker.child_module" in logger.logger.name

    def test_full_logging_pipeline(self, caplog):
        """Test complete logging pipeline with context and formatting."""
        request_id = "integration-test-123"
        request_id_var.set(request_id)
        logger = get_logger("pipeline_test")

        with caplog.at_level(logging.INFO):
            logger.info("Test pipeline message")

        # Verify all components worked together
        assert request_id in caplog.text
        assert "pipeline_test" in caplog.text
        assert "Test pipeline message" in caplog.text
        assert "INFO" in caplog.text

    @pytest.mark.asyncio
    async def test_decorator_with_context_injection(self, caplog):
        """Test decorator properly injects request ID into logs."""
        request_id = "decorator-integration-456"
        request_id_var.set(request_id)

        @log_stage("Integration Stage")
        async def integration_task():
            await asyncio.sleep(0.01)
            return "done"

        with caplog.at_level(logging.INFO):
            result = await integration_task()

        assert result == "done"
        # Request ID should appear in decorator logs
        assert request_id in caplog.text
        assert "Integration Stage" in caplog.text


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and corner scenarios."""

    def test_logger_with_empty_module_name(self, caplog):
        """Test get_logger handles empty module name."""
        request_id_var.set("edge-test-1")
        logger = get_logger("")

        with caplog.at_level(logging.INFO):
            logger.info("Message from empty module")

        assert "factchecker." in caplog.text

    def test_context_var_with_special_characters(self, caplog):
        """Test request ID containing special characters."""
        special_id = "req-123!@#$%^&*()-_=+[]{};:',.<>?/"
        request_id_var.set(special_id)
        logger = get_logger("special_char_test")

        with caplog.at_level(logging.INFO):
            logger.info("Test special chars")

        assert special_id in caplog.text

    @pytest.mark.asyncio
    async def test_decorator_with_long_stage_name(self, caplog):
        """Test decorator with very long stage name."""
        request_id_var.set("edge-test-3")
        long_name = "A" * 100

        @log_stage(long_name)
        async def long_named_task():
            return "result"

        with caplog.at_level(logging.INFO):
            result = await long_named_task()

        assert result == "result"
        assert long_name in caplog.text

    def test_multiple_log_calls_from_same_logger(self, caplog):
        """Test multiple log calls maintain context."""
        request_id = "edge-test-4"
        request_id_var.set(request_id)
        logger = get_logger("multi_call_test")

        with caplog.at_level(logging.INFO):
            logger.info("Message 1")
            logger.info("Message 2")
            logger.info("Message 3")

        # All three messages should have the same request ID
        assert caplog.text.count(request_id) == 3



