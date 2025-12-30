"""
Query optimization for search.

Converts user questions into optimized search queries
for different data sources (PubMed MeSH terms, semantic search, etc.)
"""
from app.core.logging import get_logger
from app.schemas.retrieval import OptimizedQueries
from app.schemas.events import ProgressStep
from app.services.llm import get_llm
from .types import ProgressCallback, _noop_callback

logger = get_logger(__name__)


def optimize_query(
    user_query: str, 
    on_progress: ProgressCallback = _noop_callback
) -> OptimizedQueries:
    """
    Convert user question into optimized search queries for PubMed and Semantic Scholar.
    
    Uses an LLM to generate:
    - PubMed query with MeSH terms and boolean operators
    - Semantic query for natural language search
    - Key concepts for concept-based search
    
    Args:
        user_query: The research question from the user
        on_progress: Callback for progress updates
        
    Returns:
        OptimizedQueries with pubmed_query, semantic_query, and key_concepts
    """
    on_progress(ProgressStep.OPTIMIZING, "Optimizing search queries...", None)
    
    llm = get_llm().with_structured_output(OptimizedQueries)
    
    prompt = f"""Convert this research question into comprehensive, optimized search queries.

User question: {user_query}

CRITICAL REQUIREMENTS:
1. If the question contains specific numbers, dosages, or time durations (like "7-8 hours", "500mg", "3 times per week"), YOU MUST include these in BOTH queries.
2. Include SYNONYMS and RELATED TERMS for the main concepts.
3. Think about the UNDERLYING MECHANISMS and include those terms too.

For PubMed query:
- Use MeSH terms where appropriate (e.g., "fasting"[MeSH], "insulin resistance"[MeSH])
- Use AND/OR boolean operators to combine concepts
- Include ALL relevant synonyms (e.g., for "intermittent fasting" also include "time-restricted eating", "alternate day fasting")
- Add mechanism-related terms (e.g., for fasting: "autophagy", "insulin sensitivity", "ketosis", "metabolic switch")

For Semantic Search query:
- Use natural scientific language with comprehensive terminology
- Include mechanism-related terms and biological pathways
- Add related outcome measures and biomarkers

For Key Concepts (extract 5-8 terms):
- Include the main topic
- Include specific mechanisms (e.g., "autophagy", "mTOR", "AMPK")
- Include relevant biomarkers (e.g., "cortisol", "insulin", "glucose")
- Include related interventions or treatments
- Include outcome measures

EXAMPLE for "intermittent fasting metabolic health":
- PubMed: (intermittent fasting[MeSH] OR time-restricted feeding OR alternate day fasting) AND (metabolic health[MeSH] OR insulin sensitivity OR glucose metabolism OR autophagy)
- Semantic: intermittent fasting metabolic effects insulin sensitivity glucose regulation autophagy ketosis circadian rhythm
- Concepts: ["intermittent fasting", "insulin sensitivity", "autophagy", "glucose metabolism", "ketosis", "circadian rhythm", "metabolic syndrome"]"""

    result = llm.invoke(prompt)
    logger.info("QUERY OPTIMIZATION")
    logger.debug(f"PubMed: {result.pubmed_query}")
    logger.debug(f"Semantic: {result.semantic_query}")
    logger.debug(f"Concepts: {result.key_concepts}")
    return result
