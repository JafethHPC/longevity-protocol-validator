"""
SSE Event Schemas

Pydantic models for Server-Sent Events during report generation.
These define the structure of progress updates sent to the frontend.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum


class ProgressStep(str, Enum):
    """All possible steps in the research pipeline."""
    OPTIMIZING = "optimizing"
    SEARCHING_PUBMED = "searching_pubmed"
    SEARCHING_OPENALEX = "searching_openalex"
    SEARCHING_EUROPEPMC = "searching_europepmc"
    SEARCHING_CROSSREF = "searching_crossref"
    CONCEPT_SEARCH = "concept_search"
    DEDUPLICATING = "deduplicating"
    RANKING = "ranking"
    FILTERING = "filtering"
    GENERATING_FINDINGS = "generating_findings"
    EXTRACTING_PROTOCOLS = "extracting_protocols"
    COMPLETE = "complete"


class ProgressEvent(BaseModel):
    """Progress update during report generation."""
    type: Literal["progress"] = "progress"
    step: ProgressStep
    message: str = Field(description="Human-readable status message")
    detail: Optional[str] = Field(default=None, description="Additional detail like 'Found 25 papers'")
    progress_percent: int = Field(ge=0, le=100, description="Overall progress percentage")


class ErrorEvent(BaseModel):
    """Error event when something fails."""
    type: Literal["error"] = "error"
    message: str
    step: Optional[ProgressStep] = None


class CompleteEvent(BaseModel):
    """Completion event with report ID."""
    type: Literal["complete"] = "complete"
    report_id: str


STEP_CONFIG = {
    ProgressStep.OPTIMIZING: {"label": "Optimizing search queries", "progress": 5},
    ProgressStep.SEARCHING_PUBMED: {"label": "Searching PubMed", "progress": 15},
    ProgressStep.SEARCHING_OPENALEX: {"label": "Searching OpenAlex", "progress": 25},
    ProgressStep.SEARCHING_EUROPEPMC: {"label": "Searching Europe PMC", "progress": 35},
    ProgressStep.SEARCHING_CROSSREF: {"label": "Searching CrossRef", "progress": 45},
    ProgressStep.CONCEPT_SEARCH: {"label": "Running concept searches", "progress": 55},
    ProgressStep.DEDUPLICATING: {"label": "Removing duplicates", "progress": 60},
    ProgressStep.RANKING: {"label": "Ranking by relevance", "progress": 70},
    ProgressStep.FILTERING: {"label": "Filtering with AI", "progress": 80},
    ProgressStep.GENERATING_FINDINGS: {"label": "Generating findings", "progress": 90},
    ProgressStep.EXTRACTING_PROTOCOLS: {"label": "Extracting protocols", "progress": 95},
    ProgressStep.COMPLETE: {"label": "Complete", "progress": 100},
}
