"""
Report Schemas

All Pydantic models related to research reports:
- API request/response models
- LLM structured output models
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
    has_fulltext: bool = False
    source_type: str = "paper"  # "paper" or "clinical_trial"


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
    """Complete structured research report (API response)"""
    id: str = Field(description="Unique report identifier")
    question: str = Field(description="The original research question")
    generated_at: datetime = Field(default_factory=datetime.now)
    
    executive_summary: str = Field(description="Brief 2-3 sentence summary of findings")
    key_findings: List[Finding] = Field(description="Main findings with citations")
    detailed_analysis: str = Field(description="Full analysis with inline citations [1], [2], etc.")
    protocols: List[Protocol] = Field(description="Extracted protocols/interventions")
    limitations: str = Field(description="Limitations of the available evidence")
    
    sources: List[Source] = Field(description="All sources used in the report")
    
    total_papers_searched: int = Field(default=0)
    papers_used: int = Field(default=0)


class SourceConfigRequest(BaseModel):
    """Configuration for a specific source type"""
    enabled: bool = Field(default=True, description="Whether this source is enabled")
    max_results: int = Field(default=100, ge=0, le=500, description="Maximum results to fetch")


class ReportRequest(BaseModel):
    """
    Request to generate a new report.
    
    All configuration options are optional - defaults will be used if not specified.
    This allows users to customize exactly how the research is conducted.
    """
    question: str = Field(description="The research question to investigate")
    
    # === OUTPUT LIMITS ===
    max_sources: int = Field(
        default=15, 
        ge=5, 
        le=50, 
        description="Maximum total sources in the final report"
    )
    min_clinical_trials: int = Field(
        default=3, 
        ge=0, 
        le=10, 
        description="Minimum number of clinical trials to include (if available)"
    )
    min_papers: int = Field(
        default=5, 
        ge=0, 
        le=20, 
        description="Minimum number of research papers to include"
    )
    
    # === SOURCE CONFIGURATIONS ===
    pubmed_enabled: bool = Field(default=True, description="Enable PubMed search")
    pubmed_max_results: int = Field(default=100, ge=0, le=500, description="Max PubMed results")
    
    openalex_enabled: bool = Field(default=True, description="Enable OpenAlex search")
    openalex_max_results: int = Field(default=100, ge=0, le=500, description="Max OpenAlex results")
    
    europe_pmc_enabled: bool = Field(default=True, description="Enable Europe PMC search")
    europe_pmc_max_results: int = Field(default=100, ge=0, le=500, description="Max Europe PMC results")
    
    crossref_enabled: bool = Field(default=True, description="Enable CrossRef search")
    crossref_max_results: int = Field(default=100, ge=0, le=500, description="Max CrossRef results")
    
    clinical_trials_enabled: bool = Field(default=True, description="Enable ClinicalTrials.gov search")
    clinical_trials_max_results: int = Field(default=25, ge=0, le=100, description="Max clinical trials")
    
    # === PROCESSING OPTIONS ===
    clinical_trial_boost: float = Field(
        default=0.15, 
        ge=0.0, 
        le=0.5,
        description="Relevance score boost for clinical trials (helps them compete with highly-cited papers)"
    )
    include_fulltext: bool = Field(
        default=True,
        description="Whether to fetch full text for top papers"
    )


class FollowUpRequest(BaseModel):
    """Request for a follow-up question about an existing report"""
    report_id: str = Field(description="ID of the existing report")
    question: str = Field(description="Follow-up question")


class FindingItem(BaseModel):
    """A single finding item for LLM structured output"""
    statement: str = Field(description="The key finding or conclusion")
    source_indices: List[int] = Field(description="Paper indices supporting this finding")
    confidence: str = Field(description="low, medium, or high")


class ProtocolItem(BaseModel):
    """A single protocol item for LLM structured output"""
    name: str = Field(description="Name of the intervention/protocol")
    species: str = Field(description="Human, Mouse, Rat, etc.")
    dosage: str = Field(description="Specific dosage")
    frequency: Optional[str] = Field(default=None, description="How often")
    duration: Optional[str] = Field(default=None, description="Duration of intervention")
    result: str = Field(description="The outcome/effect")
    source_index: int = Field(description="Paper number it came from")


class ReportFindings(BaseModel):
    """Structured output for report generation"""
    executive_summary: str = Field(description="2-3 sentence summary of the key findings")
    key_findings: List[FindingItem] = Field(description="List of key findings")
    detailed_analysis: str = Field(description="Comprehensive analysis with inline citations like [1], [2]")
    limitations: str = Field(description="Limitations of the evidence and gaps in the research")


class ExtractedProtocols(BaseModel):
    """Structured output for protocol extraction"""
    protocols: List[ProtocolItem] = Field(description="List of extracted protocols")
