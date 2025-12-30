"""
Common types and utilities for the retrieval pipeline.
"""
from typing import Callable, Optional
from app.schemas.events import ProgressStep

# Type alias for progress callbacks
ProgressCallback = Callable[[ProgressStep, str, Optional[str]], None]

# Processing constants
MAX_CONCURRENT_LLM_CALLS = 5
BATCH_SIZE = 8


def _noop_callback(step: ProgressStep, message: str, detail: Optional[str] = None):
    """Default no-op callback when none provided."""
    pass
