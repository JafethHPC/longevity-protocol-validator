"""
Report Data Models

Pydantic models for structured research reports.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Source(BaseModel):
    """A research paper source"""
    index: int
    title: str
    journal: str
    year: int
    pmid: str
    abstract: str
    url: str
    citation_count: int = 0
    relevance_reason: Optional[str] = None


class Finding(BaseModel):
    """A key finding from the research"""
    statement: str = Field(description="The key finding or conclusion")
    source_indices: List[int] = Field(description="Indices of sources supporting this finding")
    confidence: str = Field(description="low, medium, or high based on evidence strength")


class Protocol(BaseModel):
    """An extracted protocol or intervention"""
    name: str
    species: str
    dosage: str
    frequency: Optional[str] = None
    duration: Optional[str] = None
    result: str
    source_index: int


class ResearchReport(BaseModel):
    """Complete structured research report"""
    id: str = Field(description="Unique report identifier")
    question: str = Field(description="The original research question")
    generated_at: datetime = Field(default_factory=datetime.now)
    
    # Report sections
    executive_summary: str = Field(description="Brief 2-3 sentence summary of findings")
    key_findings: List[Finding] = Field(description="Main findings with citations")
    detailed_analysis: str = Field(description="Full analysis with inline citations [1], [2], etc.")
    protocols: List[Protocol] = Field(description="Extracted protocols/interventions")
    limitations: str = Field(description="Limitations of the available evidence")
    
    # Sources
    sources: List[Source] = Field(description="All sources used in the report")
    
    # Metadata
    total_papers_searched: int = Field(default=0)
    papers_used: int = Field(default=0)


class ReportRequest(BaseModel):
    """Request to generate a new report"""
    question: str = Field(description="The research question to investigate")
    max_sources: int = Field(default=10, ge=5, le=20)


class FollowUpRequest(BaseModel):
    """Request for a follow-up question about an existing report"""
    report_id: str = Field(description="ID of the existing report")
    question: str = Field(description="Follow-up question")
