import re
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.schemas.paper_analysis import (
    PaperAnalysis, PaperSection, StudyMethodology, 
    ExtractedFindings, StudyLimitations, StudyType
)


SECTION_PATTERNS = [
    (r'\b(abstract)\b', 'abstract'),
    (r'\b(introduction|background)\b', 'introduction'),
    (r'\b(materials?\s*(?:and|&)?\s*methods?|methods?|study\s*design|experimental\s*(?:design|procedures?))\b', 'methods'),
    (r'\b(results?|findings?)\b', 'results'),
    (r'\b(discussion)\b', 'discussion'),
    (r'\b(conclusions?|summary)\b', 'conclusion'),
    (r'\b(references?|bibliography)\b', 'references'),
]


def identify_sections(full_text: str) -> List[PaperSection]:
    section_markers = []
    text_lower = full_text.lower()
    
    for pattern, section_type in SECTION_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            start = match.start()
            if start < 50 or full_text[max(0, start-5):start].strip() in ['', '\n', '.']:
                section_markers.append({
                    'type': section_type,
                    'start': start,
                    'name': match.group(0)
                })
    
    section_markers.sort(key=lambda x: x['start'])
    
    seen_sections = set()
    unique_markers = []
    for marker in section_markers:
        if marker['type'] not in seen_sections or marker['type'] == 'references':
            unique_markers.append(marker)
            seen_sections.add(marker['type'])
    
    sections = []
    for i, marker in enumerate(unique_markers):
        start_idx = marker['start']
        if i + 1 < len(unique_markers):
            end_idx = unique_markers[i + 1]['start']
        else:
            end_idx = len(full_text)
        
        if marker['type'] == 'references':
            continue
        
        content = full_text[start_idx:end_idx].strip()
        if len(content) > 100:
            sections.append(PaperSection(
                section_type=marker['type'],
                content=content,
                start_index=start_idx,
                end_index=end_idx
            ))
    
    if not sections:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " "]
        )
        chunks = splitter.split_text(full_text)
        
        for i, chunk in enumerate(chunks[:4]):
            sections.append(PaperSection(
                section_type=f"section_{i+1}",
                content=chunk,
                start_index=0,
                end_index=len(chunk)
            ))
    
    return sections


def extract_methodology(methods_text: str, title: str, user_query: str) -> StudyMethodology:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(StudyMethodology)
    
    prompt = f"""Extract methodology details from this research paper section.

Title: {title}
Research Question Context: {user_query}

Methods Section:
{methods_text[:6000]}

Extract:
- Study type (RCT, observational, meta-analysis, review, animal study, in vitro, case study)
- Sample size (number of participants/subjects)
- Population (who was studied)
- Intervention (what was tested)
- Control (what was the comparison)
- Duration (how long)
- Key inclusion criteria

If information is not found, leave as null."""

    try:
        return llm.invoke(prompt)
    except Exception as e:
        print(f"  Methodology extraction failed: {e}")
        return StudyMethodology(study_type=StudyType.UNKNOWN)


def extract_findings(results_text: str, title: str, user_query: str) -> ExtractedFindings:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(ExtractedFindings)
    
    prompt = f"""Extract key findings from this research paper's results section.

Title: {title}
Research Question Context: {user_query}

Results Section:
{results_text[:8000]}

Focus on extracting:
1. Main finding - the primary result in one sentence
2. Effect sizes - specific measurements with:
   - Metric name (what was measured)
   - Baseline value
   - Outcome value
   - Change (absolute or percentage)
   - P-value if available
3. Secondary findings - other notable results
4. Mechanisms - biological mechanisms mentioned

Be specific with numbers! Extract actual values, not vague descriptions."""

    try:
        return llm.invoke(prompt)
    except Exception as e:
        print(f"  Findings extraction failed: {e}")
        return ExtractedFindings(main_finding="Extraction failed")


def extract_limitations(discussion_text: str) -> StudyLimitations:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(StudyLimitations)
    
    prompt = f"""Extract limitations and conflicts of interest from this discussion/conclusion section.

Text:
{discussion_text[:4000]}

Extract:
- Limitations mentioned by the authors
- Funding sources or conflicts of interest"""

    try:
        return llm.invoke(prompt)
    except Exception as e:
        print(f"  Limitations extraction failed: {e}")
        return StudyLimitations()


def analyze_paper(
    paper: Dict, 
    user_query: str,
    full_text: Optional[str] = None
) -> Optional[PaperAnalysis]:
    title = paper.get('title', 'Unknown')
    paper_id = paper.get('pmid') or paper.get('doi') or 'unknown'
    
    text_to_analyze = full_text or paper.get('fulltext') or paper.get('abstract', '')
    
    if not text_to_analyze or len(text_to_analyze) < 200:
        return None
    
    print(f"  Analyzing: {title[:50]}...")
    
    sections = identify_sections(text_to_analyze)
    
    methods_text = ""
    results_text = ""
    discussion_text = ""
    
    for section in sections:
        if section.section_type == 'methods':
            methods_text = section.content
        elif section.section_type == 'results':
            results_text = section.content
        elif section.section_type in ['discussion', 'conclusion']:
            discussion_text += " " + section.content
    
    if not methods_text and not results_text:
        combined_text = text_to_analyze[:8000]
        methods_text = combined_text
        results_text = combined_text
        discussion_text = combined_text
    
    methodology = extract_methodology(methods_text or text_to_analyze[:3000], title, user_query)
    findings = extract_findings(results_text or text_to_analyze, title, user_query)
    limitations = extract_limitations(discussion_text or text_to_analyze[-3000:])
    
    has_fulltext = bool(full_text or paper.get('fulltext'))
    has_methodology = methodology.sample_size is not None or methodology.intervention is not None
    has_findings = len(findings.effect_sizes) > 0 or findings.main_finding != "Extraction failed"
    
    confidence = 0.3
    if has_fulltext:
        confidence += 0.3
    if has_methodology:
        confidence += 0.2
    if has_findings:
        confidence += 0.2
    
    protocol_details = None
    if methodology.intervention and methodology.duration:
        protocol_details = f"{methodology.intervention} for {methodology.duration}"
        if methodology.population:
            protocol_details += f" in {methodology.population}"
    
    return PaperAnalysis(
        title=title,
        paper_id=paper_id,
        methodology=methodology,
        findings=findings,
        limitations=limitations,
        protocol_details=protocol_details,
        clinical_implications=None,
        confidence_score=confidence
    )


def analyze_papers_batch(
    papers: List[Dict],
    user_query: str,
    max_papers: int = None,
    max_concurrent: int = 5
) -> List[PaperAnalysis]:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    if max_papers is None:
        max_papers = len(papers)
    
    papers_to_analyze = papers[:max_papers]
    total = len(papers_to_analyze)
    print(f"\n---DEEP ANALYSIS OF {total} PAPERS (parallel, {max_concurrent} concurrent)---")
    
    analyses = []
    completed = 0
    
    def analyze_with_index(args):
        idx, paper = args
        try:
            analysis = analyze_paper(paper, user_query)
            return idx, analysis, None
        except Exception as e:
            return idx, None, str(e)
    
    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        futures = {
            executor.submit(analyze_with_index, (i, paper)): i 
            for i, paper in enumerate(papers_to_analyze)
        }
        
        for future in as_completed(futures):
            idx, analysis, error = future.result()
            completed += 1
            paper_title = papers_to_analyze[idx].get('title', 'Unknown')[:40]
            
            if analysis:
                analyses.append((idx, analysis))
                print(f"  [{completed}/{total}] ✓ {paper_title}... ({analysis.confidence_score:.0%})")
            elif error:
                print(f"  [{completed}/{total}] ✗ {paper_title}... (Error: {error[:30]})")
            else:
                print(f"  [{completed}/{total}] ✗ {paper_title}... (Insufficient text)")
    
    analyses.sort(key=lambda x: x[0])
    analyses = [a[1] for a in analyses]
    
    print(f"---ANALYSIS COMPLETE: {len(analyses)} papers analyzed---")
    
    return analyses


def format_analysis_for_context(analyses: List[PaperAnalysis]) -> str:
    if not analyses:
        return ""
    
    context_parts = []
    
    for i, analysis in enumerate(analyses, 1):
        parts = [f"### Paper {i}: {analysis.title}"]
        
        m = analysis.methodology
        if m.study_type != StudyType.UNKNOWN:
            method_str = f"Study Type: {m.study_type.value.replace('_', ' ').title()}"
            if m.sample_size:
                method_str += f", N={m.sample_size}"
            if m.duration:
                method_str += f", Duration: {m.duration}"
            if m.population:
                method_str += f"\nPopulation: {m.population}"
            if m.intervention:
                method_str += f"\nIntervention: {m.intervention}"
            parts.append(method_str)
        
        f = analysis.findings
        parts.append(f"Main Finding: {f.main_finding}")
        
        if f.effect_sizes:
            effects = []
            for es in f.effect_sizes[:3]:
                effect_str = f"- {es.metric}"
                if es.change:
                    effect_str += f": {es.change}"
                if es.p_value:
                    effect_str += f" (p={es.p_value})"
                effects.append(effect_str)
            parts.append("Effect Sizes:\n" + "\n".join(effects))
        
        if f.mechanisms:
            parts.append(f"Mechanisms: {', '.join(f.mechanisms[:3])}")
        
        if analysis.protocol_details:
            parts.append(f"Protocol: {analysis.protocol_details}")
        
        parts.append(f"[Confidence: {analysis.confidence_score:.0%}]")
        
        context_parts.append("\n".join(parts))
    
    return "\n\n---\n\n".join(context_parts)
