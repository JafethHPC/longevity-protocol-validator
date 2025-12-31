"""Tests for core/exceptions.py - Custom exception hierarchy."""
import pytest


class TestBaseExceptions:
    """Test the base exception classes."""

    def test_longevity_validator_error_is_exception(self):
        """Base error should inherit from Exception."""
        from app.core.exceptions import LongevityValidatorError
        
        assert issubclass(LongevityValidatorError, Exception)

    def test_longevity_validator_error_message(self):
        """Base error should store message."""
        from app.core.exceptions import LongevityValidatorError
        
        error = LongevityValidatorError("Test error message")
        assert str(error) == "Test error message"


class TestSourceExceptions:
    """Test source-related exceptions."""

    def test_source_error_includes_source_name(self):
        """SourceError should include source name in message."""
        from app.core.exceptions import SourceError
        
        error = SourceError("PubMed", "Connection failed")
        assert "PubMed" in str(error)
        assert "Connection failed" in str(error)
        assert error.source_name == "PubMed"

    def test_source_timeout_error(self):
        """SourceTimeoutError should include timeout duration."""
        from app.core.exceptions import SourceTimeoutError
        
        error = SourceTimeoutError("OpenAlex", 30.0)
        assert "OpenAlex" in str(error)
        assert "30" in str(error)
        assert error.timeout_seconds == 30.0

    def test_source_rate_limit_error(self):
        """SourceRateLimitError should include retry_after."""
        from app.core.exceptions import SourceRateLimitError
        
        error = SourceRateLimitError("CrossRef", 60)
        assert "CrossRef" in str(error)
        assert error.retry_after == 60

    def test_source_error_hierarchy(self):
        """All source errors should inherit from SourceError."""
        from app.core.exceptions import (
            SourceError,
            SourceTimeoutError,
            SourceRateLimitError,
            SourceParseError
        )
        
        assert issubclass(SourceTimeoutError, SourceError)
        assert issubclass(SourceRateLimitError, SourceError)
        assert issubclass(SourceParseError, SourceError)


class TestReportExceptions:
    """Test report-related exceptions."""

    def test_report_generation_error(self):
        """ReportGenerationError should include phase information."""
        from app.core.exceptions import ReportGenerationError
        
        error = ReportGenerationError("retrieval", "No papers found")
        assert "retrieval" in str(error)
        assert "No papers found" in str(error)
        assert error.phase == "retrieval"

    def test_report_not_found_error(self):
        """ReportNotFoundError should include report ID."""
        from app.core.exceptions import ReportNotFoundError
        
        error = ReportNotFoundError("abc-123")
        assert "abc-123" in str(error)
        assert error.report_id == "abc-123"


class TestLLMExceptions:
    """Test LLM-related exceptions."""

    def test_llm_error_base(self):
        """LLMError should be catchable."""
        from app.core.exceptions import LLMError
        
        error = LLMError("Model returned invalid JSON")
        assert "invalid JSON" in str(error)

    def test_llm_rate_limit_error(self):
        """LLMRateLimitError should include wait time."""
        from app.core.exceptions import LLMRateLimitError
        
        error = LLMRateLimitError(60)
        assert error.wait_seconds == 60

    def test_llm_context_length_error(self):
        """LLMContextLengthError should include token counts."""
        from app.core.exceptions import LLMContextLengthError
        
        error = LLMContextLengthError(
            token_count=150000,
            max_tokens=128000
        )
        assert error.token_count == 150000
        assert error.max_tokens == 128000


class TestCacheExceptions:
    """Test cache-related exceptions."""

    def test_cache_error(self):
        """CacheError should be catchable."""
        from app.core.exceptions import CacheError
        
        error = CacheError("Connection failed")
        assert "Connection failed" in str(error)

    def test_cache_connection_error(self):
        """CacheConnectionError should include host info."""
        from app.core.exceptions import CacheConnectionError
        
        error = CacheConnectionError("localhost", 6379)
        assert "localhost" in str(error)
        assert "6379" in str(error)
