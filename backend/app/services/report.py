"""
Report Generation Service

Generates structured research reports from retrieved papers.
"""
import uuid
from typing import List, Dict, Optional, Callable
from datetime import datetime
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.report import (
    ResearchReport, Source, Finding, Protocol,
    FindingItem, ProtocolItem, ReportFindings, ExtractedProtocols
)
from app.schemas.events import ProgressStep
from app.services.retrieval import enhanced_retrieval, ProgressCallback

# Default no-op callback
def _noop_callback(step: ProgressStep, message: str, detail: Optional[str] = None):
    pass


def generate_report(
    question: str, 
    max_sources: int = 10,
    on_progress: ProgressCallback = _noop_callback
) -> ResearchReport:
    """
    Generate a complete research report for a given question.
    
    Steps:
    1. Retrieve relevant papers using enhanced retrieval
    2. Generate structured findings from papers
    3. Extract protocols
    4. Compile into report
    
    Args:
        question: The research question
        max_sources: Maximum number of sources to include
        on_progress: Callback for progress updates
    """
    print(f"\n{'='*60}")
    print(f"GENERATING REPORT: {question}")
    print(f"{'='*60}\n")
    
    # 1. Retrieve papers (with progress callbacks)
    papers = enhanced_retrieval(question, max_final_papers=max_sources, on_progress=on_progress)
    
    if not papers:
        return ResearchReport(
            id=str(uuid.uuid4()),
            question=question,
            executive_summary="No relevant research papers were found for this question.",
            key_findings=[],
            detailed_analysis="Unable to provide analysis due to lack of relevant sources.",
            protocols=[],
            limitations="No papers were retrieved from the scientific databases.",
            sources=[],
            total_papers_searched=0,
            papers_used=0
        )
    
    # Convert papers to Source objects
    sources = [
        Source(
            index=i + 1,
            title=p['title'],
            journal=p.get('journal', ''),
            year=p.get('year', 0),
            pmid=p.get('pmid', ''),
            abstract=p['abstract'][:500] + "..." if len(p['abstract']) > 500 else p['abstract'],
            url=p.get('url', f"https://pubmed.ncbi.nlm.nih.gov/{p.get('pmid', '')}/"),
            citation_count=p.get('citation_count', 0),
            relevance_reason=p.get('relevance_reason')
        )
        for i, p in enumerate(papers)
    ]
    
    # 2. Build context for LLM
    context = _build_context(papers)
    
    # 3. Generate findings
    on_progress(ProgressStep.GENERATING_FINDINGS, "Generating research findings...", f"Analyzing {len(papers)} papers")
    findings_data = _generate_findings(question, context)
    
    # 4. Extract protocols
    on_progress(ProgressStep.EXTRACTING_PROTOCOLS, "Extracting protocols...", None)
    protocols_data = _extract_protocols(question, context)
    
    # 5. Compile report
    key_findings = [
        Finding(
            statement=f.statement,
            source_indices=f.source_indices,
            confidence=f.confidence
        )
        for f in findings_data.key_findings
    ]
    
    protocols = [
        Protocol(
            name=p.name,
            species=p.species,
            dosage=p.dosage,
            frequency=p.frequency,
            duration=p.duration,
            result=p.result,
            source_index=p.source_index
        )
        for p in protocols_data.protocols
    ]
    
    report = ResearchReport(
        id=str(uuid.uuid4()),
        question=question,
        executive_summary=findings_data.executive_summary,
        key_findings=key_findings,
        detailed_analysis=findings_data.detailed_analysis,
        protocols=protocols,
        limitations=findings_data.limitations,
        sources=sources,
        total_papers_searched=len(papers) * 5,  # Approximate
        papers_used=len(papers)
    )
    
    print(f"\n---REPORT GENERATED---")
    print(f"  Sources: {len(sources)}")
    print(f"  Findings: {len(key_findings)}")
    print(f"  Protocols: {len(protocols)}")
    
    return report


def _build_context(papers: List[Dict]) -> str:
    """Build context string from papers for LLM."""
    context_parts = []
    for i, paper in enumerate(papers, 1):
        context_parts.append(f"""
[Paper {i}]
Title: {paper['title']}
Journal: {paper.get('journal', 'N/A')} ({paper.get('year', 'N/A')})
Abstract: {paper['abstract']}
""")
    return "\n".join(context_parts)


def _generate_findings(question: str, context: str) -> ReportFindings:
    """Generate structured findings from papers."""
    print("---GENERATING FINDINGS---")
    
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(ReportFindings, strict=False)
    
    prompt = f"""You are a scientific research analyst. Based on the following research papers, generate a comprehensive report answering the question.

IMPORTANT RULES:
1. ONLY use information explicitly stated in the papers
2. Use inline citations like [1], [2] referring to paper numbers
3. If papers don't fully answer the question, acknowledge this
4. Rate confidence based on: number of supporting studies, study quality, consistency of findings

QUESTION: {question}

RESEARCH PAPERS:
{context}

Generate a structured report with:
- Executive summary (2-3 sentences)
- Key findings (each with source indices and confidence level)
- Detailed analysis (comprehensive with inline citations)
- Limitations of the evidence"""

    return llm.invoke(prompt)


def _extract_protocols(question: str, context: str) -> ExtractedProtocols:
    """Extract protocols/interventions from papers."""
    print("---EXTRACTING PROTOCOLS---")
    
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(ExtractedProtocols, strict=False)
    
    prompt = f"""Extract all specific protocols, interventions, or dosages mentioned in these research papers.

For each protocol, extract:
- name: Name of the intervention/protocol
- species: Human, Mouse, Rat, etc.
- dosage: Specific dosage if mentioned
- frequency: How often (if mentioned)
- duration: Duration of intervention (if mentioned)
- result: The outcome/effect
- source_index: Which paper number it came from

Only extract protocols with specific, actionable information. Skip vague recommendations.

QUESTION CONTEXT: {question}

RESEARCH PAPERS:
{context}"""

    return llm.invoke(prompt)


def generate_followup_answer(report: ResearchReport, followup_question: str) -> str:
    """Answer a follow-up question using the report's sources."""
    print(f"---ANSWERING FOLLOW-UP: {followup_question}---")
    
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    )
    
    sources_context = "\n\n".join([
        f"[{s.index}] {s.title}\n{s.abstract}"
        for s in report.sources
    ])
    
    prompt = f"""Based on the research sources from a previous report, answer this follow-up question.

ORIGINAL QUESTION: {report.question}

EXECUTIVE SUMMARY FROM REPORT:
{report.executive_summary}

AVAILABLE SOURCES:
{sources_context}

FOLLOW-UP QUESTION: {followup_question}

RULES:
1. Only use information from the provided sources
2. Use inline citations [1], [2], etc.
3. If the sources don't contain relevant information, say so clearly
4. Be concise but comprehensive"""

    response = llm.invoke(prompt)
    return response.content
