import uuid
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.report import (
    ResearchReport, Source, Finding, Protocol,
    ReportFindings, ExtractedProtocols
)
from app.schemas.retrieval import ResearchConfig
from app.schemas.events import ProgressStep
from app.services.retrieval import enhanced_retrieval, ProgressCallback
from app.services.paper_analysis import analyze_papers_batch, format_analysis_for_context


def _noop_callback(step: ProgressStep, message: str, detail: Optional[str] = None):
    pass


def generate_report(
    question: str, 
    max_sources: int = 25,
    config: Optional[ResearchConfig] = None,
    on_progress: ProgressCallback = _noop_callback
) -> ResearchReport:
    """
    Generate a complete research report for the given question.
    
    Args:
        question: The research question to investigate
        max_sources: Maximum number of sources in the final report (overridden by config if provided)
        config: ResearchConfig controlling source quantities and types
        on_progress: Callback for progress updates
    """
    print(f"\n{'='*60}")
    print(f"GENERATING REPORT: {question}")
    print(f"{'='*60}\n")
    
    papers = enhanced_retrieval(
        question, 
        max_final_papers=max_sources, 
        config=config,
        on_progress=on_progress
    )
    
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
    
    sources = []
    for i, p in enumerate(papers):
        # Determine if this is a clinical trial
        is_trial = p.get('type') == 'clinical_trial' or p.get('pmid', '').startswith('NCT')
        
        # For clinical trials, use ClinicalTrials.gov URL
        if is_trial:
            nct_id = p.get('pmid', '')
            url = p.get('url', f"https://clinicaltrials.gov/study/{nct_id}")
        else:
            url = p.get('url', f"https://pubmed.ncbi.nlm.nih.gov/{p.get('pmid', '')}/")
        
        sources.append(Source(
            index=i + 1,
            title=p['title'],
            journal=p.get('journal', ''),
            year=p.get('year', 0),
            pmid=p.get('pmid', ''),
            abstract=p['abstract'][:500] + "..." if len(p['abstract']) > 500 else p['abstract'],
            url=url,
            citation_count=p.get('citation_count', 0),
            relevance_reason=p.get('relevance_reason'),
            has_fulltext=p.get('has_fulltext', False),
            source_type="clinical_trial" if is_trial else "paper"
        ))
    
    on_progress(ProgressStep.ANALYZING_PAPERS, "Analyzing papers in depth...", f"Extracting structured data from {len(papers)} papers")
    
    analyses = analyze_papers_batch(papers, question, max_papers=len(papers))
    
    context = _build_context(papers, analyses)
    
    on_progress(ProgressStep.GENERATING_FINDINGS, "Generating research findings...", f"Synthesizing insights")
    findings_data = _generate_findings(question, context)
    
    on_progress(ProgressStep.EXTRACTING_PROTOCOLS, "Extracting protocols...", None)
    protocols_data = _extract_protocols(question, context)
    
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
        total_papers_searched=len(papers) * 5,
        papers_used=len(papers)
    )
    
    print(f"\n---REPORT GENERATED---")
    print(f"  Sources: {len(sources)}")
    print(f"  Findings: {len(key_findings)}")
    print(f"  Protocols: {len(protocols)}")
    print(f"  Deep analyses: {len(analyses)}")
    
    return report


def _build_context(papers: List[Dict], analyses=None) -> str:
    context_parts = []
    fulltext_count = 0
    
    analysis_context = ""
    if analyses:
        analysis_context = format_analysis_for_context(analyses)
        context_parts.append("## STRUCTURED PAPER ANALYSES\n\n" + analysis_context)
        context_parts.append("\n\n## RAW PAPER DATA\n")
    
    for i, paper in enumerate(papers, 1):
        if paper.get('has_fulltext') and paper.get('fulltext'):
            content = paper['fulltext'][:15000]
            content_type = "Full Text"
            fulltext_count += 1
        else:
            content = paper.get('abstract', 'No abstract available.')
            content_type = "Abstract"
        
        context_parts.append(f"""
[Paper {i}] ({content_type})
Title: {paper['title']}
Journal: {paper.get('journal', 'N/A')} ({paper.get('year', 'N/A')})
{content_type}: {content}
""")
    
    print(f"  Context built: {fulltext_count} with full text, {len(papers) - fulltext_count} with abstract only")
    if analyses:
        print(f"  Structured analyses included: {len(analyses)}")
    
    return "\n".join(context_parts)


def _generate_findings(question: str, context: str) -> ReportFindings:
    print("---GENERATING FINDINGS---")
    
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(ReportFindings, strict=False)
    
    prompt = f"""You are a scientific research analyst. Generate a comprehensive, well-cited research report.

QUESTION: {question}

RESEARCH DATA:
{context[:80000]}

CRITICAL REQUIREMENTS:
1. Use inline citations like [1], [2], [3] for EVERY factual claim
2. Use the STRUCTURED ANALYSES section for precise effect sizes, protocols, and mechanisms
3. Include SPECIFIC NUMBERS: percentages, dosages, sample sizes, p-values from the analyses
4. When multiple papers support a finding, cite ALL of them: [1, 3, 5]

CONTENT REQUIREMENTS:
1. MECHANISMS: Include underlying biological/physiological mechanisms
2. EFFECT SIZES: Quote specific measurements (e.g., "12.3% improvement in HOMA-IR")
3. PROTOCOLS: Include specific dosages, durations, and populations
4. SYNTHESIZE: Compare and contrast findings from different studies
5. NUANCE: Note conflicting results and populations where effects differ

STRUCTURE:
- Executive summary: 2-3 impactful sentences with key numbers
- Key findings: 4-6 distinct findings with specific data, each with:
  - A clear statement with numbers
  - Source indices
  - Confidence level
- Detailed analysis: 
  - 400-600 words with heavy citations
  - Include effect sizes and protocol specifics
  - Discuss mechanisms
- Limitations: What gaps exist? What populations/aspects need more study?

QUALITY CHECKLIST:
✓ Specific numbers/measurements included
✓ Protocol details (dosage, duration) mentioned
✓ Mechanisms explained
✓ Multiple papers synthesized
✓ Limitations acknowledged"""

    return llm.invoke(prompt)


def _extract_protocols(question: str, context: str) -> ExtractedProtocols:
    print("---EXTRACTING PROTOCOLS---")
    
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(ExtractedProtocols, strict=False)
    
    prompt = f"""Extract ACTIONABLE protocols that answer the research question. Focus on interventions that could be practically implemented.

RESEARCH QUESTION: {question}

CRITICAL RULES - DO NOT EXTRACT:
❌ Surgical procedures used to create disease models (e.g., "bilateral olfactory bulbectomy", "sciatic nerve ligation")
❌ Laboratory techniques (e.g., "fecal microbiota transplantation in mice", "gene knockouts")
❌ Disease induction methods (e.g., "high-fat diet to induce obesity in rats")
❌ Diagnostic procedures without treatment value
❌ Protocols without specific dosages or durations

PRIORITIZE EXTRACTING:
✓ Human clinical protocols with specific dosages
✓ Supplements, medications, or lifestyle interventions
✓ Protocols with measurable outcomes and effect sizes
✓ Interventions directly relevant to the research question

For each protocol, provide:
- name: Specific intervention name (e.g., "Lactobacillus rhamnosus GG supplementation")
- species: PRIORITIZE Human studies; only include animal studies if highly relevant
- dosage: MUST be specific (e.g., "10 billion CFU/day", "500mg twice daily") - skip if not available
- frequency: How often administered
- duration: Length of intervention
- result: Quantitative outcome with numbers (e.g., "32% reduction in depression scores, p<0.01")
- source_index: Paper reference number

QUALITY FILTER: Only include protocols that:
1. Are directly relevant to answering "{question}"
2. Have specific, actionable dosages
3. Show measurable results
4. Could realistically be implemented

RESEARCH DATA:
{context[:60000]}"""

    return llm.invoke(prompt)


def generate_followup_answer(report: ResearchReport, followup_question: str) -> str:
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
