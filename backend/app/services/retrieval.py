"""
Enhanced Multi-Source Retrieval System

Provides improved paper retrieval by:
1. Optimizing search queries for each source
2. Fetching from multiple sources (PubMed, OpenAlex, Europe PMC, CrossRef)
3. Ranking by semantic similarity + citation count
4. LLM-based relevance filtering
"""
from typing import List, Dict
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import numpy as np

from app.core.config import settings
from app.schemas.retrieval import OptimizedQueries, PaperRelevance
from app.services.sources import (
    search_pubmed,
    search_openalex,
    search_europe_pmc,
    search_crossref,
)


def optimize_query(user_query: str) -> OptimizedQueries:
    """Convert user question into optimized search queries for PubMed and Semantic Scholar."""
    llm = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0, 
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(OptimizedQueries)
    
    prompt = f"""Convert this research question into optimized search queries.

User question: {user_query}

CRITICAL: If the question contains specific numbers, dosages, or time durations (like "7-8 hours", "500mg", "3 times per week"), YOU MUST include these in BOTH queries. These specifics are essential for finding the right papers.

For PubMed:
- PRESERVE any specific numbers/dosages from the question
- Use MeSH terms where appropriate (e.g., "sleep"[MeSH], "longevity"[MeSH])
- Use AND/OR boolean operators
- Include common synonyms

For Semantic Search:
- PRESERVE any specific numbers/dosages from the question
- Use natural scientific language
- Include key concepts and synonyms

Extract the main scientific concepts (3-5 key terms including any specific values)."""

    result = llm.invoke(prompt)
    print(f"---QUERY OPTIMIZATION---")
    print(f"  PubMed: {result.pubmed_query}")
    print(f"  Semantic: {result.semantic_query}")
    print(f"  Concepts: {result.key_concepts}")
    return result


def deduplicate_papers(papers: List[Dict]) -> List[Dict]:
    """Remove duplicate papers based on title similarity and PMID."""
    seen_titles = set()
    seen_pmids = set()
    unique_papers = []
    
    for paper in papers:
        # Check PMID first (most reliable for identifying duplicates)
        pmid = paper.get('pmid', '')
        if pmid and pmid in seen_pmids:
            continue
        
        # Check title similarity
        title_key = paper['title'].lower().strip()[:60]
        if title_key in seen_titles:
            continue
        
        # Add to seen sets
        if pmid:
            seen_pmids.add(pmid)
        seen_titles.add(title_key)
        unique_papers.append(paper)
    
    return unique_papers


def rank_by_relevance(papers: List[Dict], query: str, top_k: int = 20) -> List[Dict]:
    """Rank papers by semantic similarity to the query + citation count."""
    if not papers:
        return []
    
    print(f"---RANKING {len(papers)} PAPERS BY RELEVANCE---")
    
    embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
    
    query_embedding = embeddings.embed_query(query)
    paper_texts = [f"{p['title']}. {p['abstract'][:500]}" for p in papers]
    paper_embeddings = embeddings.embed_documents(paper_texts)
    
    query_vec = np.array(query_embedding)
    
    for i, paper in enumerate(papers):
        paper_vec = np.array(paper_embeddings[i])
        similarity = np.dot(query_vec, paper_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(paper_vec)
        )
        
        citation_boost = min(paper['citation_count'] / 1000, 0.2)
        review_boost = 0.1 if paper['is_review'] else 0
        paper['relevance_score'] = similarity + citation_boost + review_boost
    
    ranked = sorted(papers, key=lambda x: x['relevance_score'], reverse=True)
    
    print(f"  Top 5 after ranking:")
    for p in ranked[:5]:
        print(f"    [{p['relevance_score']:.3f}] {p['title'][:60]}...")
    
    return ranked[:top_k]


def filter_by_llm_relevance(papers: List[Dict], user_query: str, max_papers: int = 10) -> List[Dict]:
    """Use LLM to filter papers based on actual relevance to the question."""
    if len(papers) <= max_papers:
        return papers
    
    print(f"---LLM FILTERING {len(papers)} PAPERS---")
    
    llm = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0, 
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(PaperRelevance)
    
    relevant_papers = []
    
    for paper in papers:
        prompt = f"""Is this paper relevant to answering the research question?

QUESTION: {user_query}

PAPER TITLE: {paper['title']}
ABSTRACT: {paper['abstract'][:800]}

A paper is relevant if it contains information that could help answer the question.
Be inclusive - if there's useful related information, mark as relevant."""
        
        try:
            result = llm.invoke(prompt)
            if result.is_relevant:
                paper['relevance_reason'] = result.reason
                relevant_papers.append(paper)
                print(f"  [+] {paper['title'][:50]}... - {result.reason[:50]}")
            else:
                print(f"  [-] {paper['title'][:50]}...")
            
            if len(relevant_papers) >= max_papers:
                break
                
        except Exception as e:
            print(f"  Error evaluating paper: {e}")
            relevant_papers.append(paper)
    
    print(f"  Filtered to {len(relevant_papers)} relevant papers")
    return relevant_papers


def enhanced_retrieval(user_query: str, max_final_papers: int = 10) -> List[Dict]:
    """
    Full enhanced retrieval pipeline:
    1. Optimize query
    2. Search multiple sources
    3. Deduplicate
    4. Rank by relevance
    5. LLM filter
    
    Args:
        user_query: The research question from the user
        max_final_papers: Maximum number of papers to return
    """
    print(f"\n{'='*60}")
    print(f"ENHANCED RETRIEVAL: {user_query}")
    print(f"Target papers: {max_final_papers}")
    print(f"{'='*60}\n")
    
    optimized = optimize_query(user_query)
    
    # Search 4 reliable sources
    per_source_max = 30
    
    print(f"---SEARCH LIMITS: {per_source_max} papers per source---")
    print(f"---SOURCES: PubMed, OpenAlex, Europe PMC, CrossRef---")
    
    # Primary searches with optimized queries
    pubmed_papers = search_pubmed(optimized.pubmed_query, max_results=per_source_max)
    openalex_papers = search_openalex(optimized.semantic_query, max_results=per_source_max)
    europepmc_papers = search_europe_pmc(optimized.semantic_query, max_results=per_source_max)
    crossref_papers = search_crossref(optimized.semantic_query, max_results=per_source_max)
    
    # Additional concept-based searches for better coverage
    concept_query = " ".join(optimized.key_concepts[:3])
    print(f"---CONCEPT SEARCH: {concept_query}---")
    
    pubmed_concept = search_pubmed(concept_query, max_results=per_source_max)
    openalex_concept = search_openalex(concept_query, max_results=per_source_max)
    
    # Combine all sources
    all_papers = (
        pubmed_papers + 
        openalex_papers + 
        europepmc_papers + 
        crossref_papers +
        pubmed_concept +
        openalex_concept
    )
    print(f"\n---TOTAL CANDIDATES: {len(all_papers)}---")
    
    if not all_papers:
        return []
    
    unique_papers = deduplicate_papers(all_papers)
    print(f"---AFTER DEDUP: {len(unique_papers)}---")
    
    # Rank more papers to give LLM filter a better pool
    top_k_for_ranking = min(len(unique_papers), max_final_papers * 2)
    ranked_papers = rank_by_relevance(unique_papers, user_query, top_k=top_k_for_ranking)
    final_papers = filter_by_llm_relevance(ranked_papers, user_query, max_papers=max_final_papers)
    
    print(f"\n---FINAL PAPERS: {len(final_papers)}---")
    for i, p in enumerate(final_papers, 1):
        print(f"  {i}. [{p['year']}] {p['title'][:60]}...")
        print(f"     Source: {p['source']}, Citations: {p['citation_count']}, PMID: {p.get('pmid', 'N/A')}")
    
    return final_papers
