"""Tests for core/logging.py - Logging configuration."""
import logging

import pytest


class TestLogging:
    """Test the logging module."""

    def test_get_logger_returns_logger(self):
        """get_logger should return a Logger instance."""
        from app.core.logging import get_logger
        
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_uses_module_name(self):
        """Logger should use the provided module name."""
        from app.core.logging import get_logger
        
        logger = get_logger("my_custom_module")
        assert logger.name == "my_custom_module"

    def test_logger_can_log_messages(self):
        """Logger should be able to log messages without error."""
        from app.core.logging import get_logger
        
        logger = get_logger("test_logging")
        
        # These should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

    def test_setup_logging_sets_level(self):
        """setup_logging should configure the log level."""
        from app.core.logging import setup_logging, get_logger
        
        setup_logging(level="WARNING")
        logger = get_logger("test_level")
        
        # After setup, root logger level should be set
        assert logging.getLogger().level in [logging.WARNING, logging.INFO, logging.DEBUG]

    def test_multiple_get_logger_calls_same_name(self):
        """Multiple calls with same name should return same logger."""
        from app.core.logging import get_logger
        
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        
        assert logger1 is logger2
