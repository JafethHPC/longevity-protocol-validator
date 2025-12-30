"""
Custom Exceptions

Application-specific exception classes for better error handling
and more informative error messages.
"""


class LongevityValidatorError(Exception):
    """Base exception for all application errors."""
    pass


# === Data Source Errors ===

class SourceError(LongevityValidatorError):
    """Base exception for data source errors."""
    def __init__(self, source_name: str, message: str):
        self.source_name = source_name
        self.message = message
        super().__init__(f"{source_name}: {message}")


class SourceTimeoutError(SourceError):
    """Data source timed out during request."""
    def __init__(self, source_name: str, timeout_seconds: float):
        super().__init__(source_name, f"Request timed out after {timeout_seconds}s")
        self.timeout_seconds = timeout_seconds


class SourceRateLimitError(SourceError):
    """Data source rate limit exceeded."""
    def __init__(self, source_name: str, retry_after: int = None):
        msg = "Rate limit exceeded"
        if retry_after:
            msg += f", retry after {retry_after}s"
        super().__init__(source_name, msg)
        self.retry_after = retry_after


class SourceHTTPError(SourceError):
    """Data source returned an HTTP error status."""
    def __init__(self, source_name: str, status_code: int, detail: str = None):
        msg = f"HTTP {status_code}"
        if detail:
            msg += f": {detail}"
        super().__init__(source_name, msg)
        self.status_code = status_code


class SourceParseError(SourceError):
    """Failed to parse response from data source."""
    def __init__(self, source_name: str, detail: str = None):
        msg = "Failed to parse response"
        if detail:
            msg += f": {detail}"
        super().__init__(source_name, msg)


# === Report Generation Errors ===

class ReportError(LongevityValidatorError):
    """Base exception for report generation errors."""
    pass


class ReportNotFoundError(ReportError):
    """Report with given ID was not found."""
    def __init__(self, report_id: str):
        self.report_id = report_id
        super().__init__(f"Report not found: {report_id}")


class ReportGenerationError(ReportError):
    """Error during report generation."""
    def __init__(self, phase: str, message: str):
        self.phase = phase
        self.message = message
        super().__init__(f"Report generation failed during {phase}: {message}")


class InsufficientSourcesError(ReportError):
    """Not enough sources found to generate a meaningful report."""
    def __init__(self, found: int, minimum: int):
        self.found = found
        self.minimum = minimum
        super().__init__(f"Only found {found} sources, minimum required is {minimum}")


# === LLM/AI Errors ===

class LLMError(LongevityValidatorError):
    """Base exception for LLM-related errors."""
    pass


class LLMRateLimitError(LLMError):
    """OpenAI rate limit exceeded."""
    def __init__(self, retry_after: int = None):
        msg = "OpenAI rate limit exceeded"
        if retry_after:
            msg += f", retry after {retry_after}s"
        super().__init__(msg)
        self.retry_after = retry_after


class LLMContentFilterError(LLMError):
    """Content was filtered by OpenAI's safety systems."""
    def __init__(self, detail: str = None):
        msg = "Content filtered by safety systems"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


# === Cache Errors ===

class CacheError(LongevityValidatorError):
    """Base exception for cache-related errors."""
    pass


class CacheConnectionError(CacheError):
    """Failed to connect to cache backend."""
    def __init__(self, backend: str, detail: str = None):
        msg = f"Failed to connect to {backend} cache"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)
        self.backend = backend
