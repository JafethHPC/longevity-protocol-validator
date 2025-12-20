"""
Schemas Module

Contains all Pydantic models (DTOs) for:
- API request/response validation
- LLM structured outputs
- SSE streaming events
"""
from .retrieval import OptimizedQueries, PaperRelevance, PaperEvaluation, BatchPaperRelevance
from .report import (
    Source,
    Finding,
    Protocol,
    ResearchReport,
    ReportRequest,
    FollowUpRequest,
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
    "OptimizedQueries",
    "PaperRelevance",
    "PaperEvaluation",
    "BatchPaperRelevance",
    "Source",
    "Finding",
    "Protocol",
    "ResearchReport",
    "ReportRequest",
    "FollowUpRequest",
    "FindingItem",
    "ProtocolItem", 
    "ReportFindings",
    "ExtractedProtocols",
    "ProgressStep",
    "ProgressEvent",
    "ErrorEvent",
    "CompleteEvent",
    "STEP_CONFIG",
]
