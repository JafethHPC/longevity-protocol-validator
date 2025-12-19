"""
Schemas Module

Contains all Pydantic models (DTOs) for:
- API request/response validation
- LLM structured outputs

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
]
