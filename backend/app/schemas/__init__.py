"""
Schemas Module

Contains all Pydantic models (DTOs) for:
- API request/response validation
- LLM structured outputs
- SSE streaming events

Note: If you add a database later, ORM models would go in app/models/
"""
from .retrieval import OptimizedQueries, PaperRelevance
from .report import (
    # Core data models
    Source,
    Finding,
    Protocol,
    ResearchReport,
    # API requests
    ReportRequest,
    FollowUpRequest,
    # LLM structured outputs
    FindingItem,
    ProtocolItem,
    ReportFindings,
    ExtractedProtocols,
)
from .events import (
    ProgressStep,
    ProgressEvent,
    ErrorEvent,
    CompleteEvent,
    STEP_CONFIG,
)

__all__ = [
    # Retrieval schemas
    "OptimizedQueries",
    "PaperRelevance",
    # Report - Core models
    "Source",
    "Finding",
    "Protocol",
    "ResearchReport",
    # Report - API requests
    "ReportRequest",
    "FollowUpRequest",
    # Report - LLM outputs
    "FindingItem",
    "ProtocolItem", 
    "ReportFindings",
    "ExtractedProtocols",
    # Events
    "ProgressStep",
    "ProgressEvent",
    "ErrorEvent",
    "CompleteEvent",
    "STEP_CONFIG",
]
