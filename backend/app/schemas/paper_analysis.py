from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class StudyType(str, Enum):
    RCT = "randomized_controlled_trial"
    OBSERVATIONAL = "observational"
    META_ANALYSIS = "meta_analysis"
    REVIEW = "review"
    ANIMAL = "animal_study"
    IN_VITRO = "in_vitro"
    CASE_STUDY = "case_study"
    UNKNOWN = "unknown"


class EffectSize(BaseModel):
    metric: str = Field(description="Name of the measured outcome (e.g., HOMA-IR, HbA1c, LDL)")
    baseline: Optional[str] = Field(default=None, description="Baseline/control value")
    outcome: Optional[str] = Field(default=None, description="Post-intervention value")
    change: Optional[str] = Field(default=None, description="Absolute or percentage change")
    p_value: Optional[str] = Field(default=None, description="Statistical significance")


class StudyMethodology(BaseModel):
    study_type: StudyType = Field(description="Type of study design")
    sample_size: Optional[int] = Field(default=None, description="Number of participants")
    population: Optional[str] = Field(default=None, description="Description of study population")
    intervention: Optional[str] = Field(default=None, description="What intervention was tested")
    control: Optional[str] = Field(default=None, description="Control/placebo description")
    duration: Optional[str] = Field(default=None, description="Study duration")
    key_inclusion_criteria: Optional[str] = Field(default=None, description="Main inclusion criteria")


class ExtractedFindings(BaseModel):
    main_finding: str = Field(description="The primary finding in one sentence")
    effect_sizes: List[EffectSize] = Field(default=[], description="Quantitative outcomes with measurements")
    secondary_findings: List[str] = Field(default=[], description="Other notable findings")
    mechanisms: List[str] = Field(default=[], description="Biological mechanisms mentioned")


class StudyLimitations(BaseModel):
    limitations: List[str] = Field(default=[], description="Study limitations mentioned")
    conflicts_of_interest: Optional[str] = Field(default=None, description="Funding or conflicts")


class PaperAnalysis(BaseModel):
    title: str
    paper_id: str
    methodology: StudyMethodology
    findings: ExtractedFindings
    limitations: StudyLimitations
    protocol_details: Optional[str] = Field(default=None, description="Specific protocol/dosage details if applicable")
    clinical_implications: Optional[str] = Field(default=None, description="Practical implications mentioned")
    confidence_score: float = Field(default=0.5, ge=0, le=1, description="How confident we are in this analysis (0-1)")


class PaperSection(BaseModel):
    section_type: str = Field(description="Section name: abstract, introduction, methods, results, discussion, conclusion")
    content: str = Field(description="Text content of this section")
    start_index: int = Field(description="Character start position in original text")
    end_index: int = Field(description="Character end position in original text")
