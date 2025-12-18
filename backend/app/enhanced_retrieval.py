"""
Enhanced Multi-Source Retrieval System

This module provides improved paper retrieval by:
1. Optimizing search queries for each source
2. Fetching from multiple sources (PubMed, Semantic Scholar)
3. Ranking by semantic similarity + citation count
4. LLM-based relevance filtering
"""

import requests
import time
from typing import List, Dict, Optional
from Bio import Entrez
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field
import ssl
import numpy as np

from app.core.config import settings

ssl._create_default_https_context = ssl._create_unverified_context
Entrez.email = "researcher@example.com"


# ============================================================
# 1. QUERY OPTIMIZATION
# ============================================================

class OptimizedQueries(BaseModel):
    """Structured output for query optimization"""
    pubmed_query: str = Field(description="Optimized query for PubMed with MeSH terms and boolean operators")
    semantic_query: str = Field(description="Natural language query optimized for semantic search")
    key_concepts: List[str] = Field(description="Key scientific concepts from the query")


def optimize_query(user_query: str) -> OptimizedQueries:
    """
    Use GPT to convert user question into optimized search queries.
    """
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


# ============================================================
# 2. MULTI-SOURCE RETRIEVAL
# ============================================================

def search_pubmed(query: str, max_results: int = 50) -> List[Dict]:
    """Search PubMed and return papers with metadata."""
    print(f"---SEARCHING PUBMED: {query[:50]}...---")
    
    try:
        # Search for IDs
        handle = Entrez.esearch(
            db="pubmed", 
            term=query, 
            retmax=max_results,
            sort="relevance"  # Use relevance sorting
        )
        record = Entrez.read(handle)
        handle.close()
        
        ids = record.get("IdList", [])
        if not ids:
            print(f"  No results found")
            return []
        
        print(f"  Found {len(ids)} papers")
        
        # Fetch details
        handle = Entrez.efetch(db="pubmed", id=",".join(ids), retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        
        papers = []
        for paper in records.get('PubmedArticle', []):
            try:
                article = paper['MedlineCitation']['Article']
                abstract_list = article.get('Abstract', {}).get('AbstractText', [])
                abstract = " ".join(str(a) for a in abstract_list)
                
                if not abstract or len(abstract) < 100:
                    continue
                
                # Check if it's a review (these are often more useful)
                pub_types = article.get('PublicationTypeList', [])
                pub_type_names = [str(pt) for pt in pub_types]
                is_review = any('review' in pt.lower() for pt in pub_type_names)
                
                papers.append({
                    "title": str(article['ArticleTitle']),
                    "abstract": abstract,
                    "journal": str(article['Journal']['Title']),
                    "year": int(article['Journal']['JournalIssue']['PubDate'].get('Year', 0)),
                    "pmid": str(paper['MedlineCitation']['PMID']),
                    "source": "PubMed",
                    "is_review": is_review,
                    "citation_count": 0,  # Will be updated if available
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{paper['MedlineCitation']['PMID']}/"
                })
            except (KeyError, TypeError):
                continue
        
        print(f"  Returned {len(papers)} papers with abstracts")
        return papers
        
    except Exception as e:
        print(f"  PubMed error: {e}")
        return []


def search_semantic_scholar(query: str, max_results: int = 50) -> List[Dict]:
    """Search Semantic Scholar API for papers."""
    print(f"---SEARCHING SEMANTIC SCHOLAR: {query[:50]}...---")
    
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": min(max_results, 100),  # API limit
        "fields": "title,abstract,year,citationCount,journal,externalIds,publicationTypes"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 429:
            print("  Rate limited, waiting 3 seconds...")
            time.sleep(3)
            response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"  Error: {response.status_code}")
            return []
        
        data = response.json()
        papers = []
        
        for paper in data.get("data", []):
            abstract = paper.get("abstract", "")
            if not abstract or len(abstract) < 100:
                continue
            
            pub_types = paper.get("publicationTypes", []) or []
            is_review = "Review" in pub_types
            
            pmid = paper.get("externalIds", {}).get("PubMed", "")
            
            papers.append({
                "title": paper.get("title", ""),
                "abstract": abstract,
                "journal": paper.get("journal", {}).get("name", "") if paper.get("journal") else "",
                "year": paper.get("year", 0) or 0,
                "pmid": pmid,
                "source": "SemanticScholar",
                "is_review": is_review,
                "citation_count": paper.get("citationCount", 0) or 0,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
            })
        
        print(f"  Returned {len(papers)} papers with abstracts")
        return papers
        
    except Exception as e:
        print(f"  Semantic Scholar error: {e}")
        return []


def deduplicate_papers(papers: List[Dict]) -> List[Dict]:
    """Remove duplicate papers based on title similarity."""
    seen_titles = set()
    unique_papers = []
    
    for paper in papers:
        # Normalize title for comparison
        title_key = paper['title'].lower().strip()[:60]
        
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_papers.append(paper)
    
    return unique_papers


# ============================================================
# 3. RELEVANCE RANKING (Embedding-based)
# ============================================================

def rank_by_relevance(papers: List[Dict], query: str, top_k: int = 20) -> List[Dict]:
    """
    Rank papers by semantic similarity to the query + citation count.
    Uses OpenAI embeddings for similarity scoring.
    """
    if not papers:
        return []
    
    print(f"---RANKING {len(papers)} PAPERS BY RELEVANCE---")
    
    embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
    
    # Get query embedding
    query_embedding = embeddings.embed_query(query)
    
    # Get paper embeddings (using title + abstract snippet)
    paper_texts = [
        f"{p['title']}. {p['abstract'][:500]}" 
        for p in papers
    ]
    paper_embeddings = embeddings.embed_documents(paper_texts)
    
    # Calculate similarity scores
    query_vec = np.array(query_embedding)
    
    for i, paper in enumerate(papers):
        paper_vec = np.array(paper_embeddings[i])
        
        # Cosine similarity
        similarity = np.dot(query_vec, paper_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(paper_vec)
        )
        
        # Composite score: similarity + citation boost + review boost
        citation_boost = min(paper['citation_count'] / 1000, 0.2)  # Max 20% boost
        review_boost = 0.1 if paper['is_review'] else 0
        
        paper['relevance_score'] = similarity + citation_boost + review_boost
    
    # Sort by relevance score
    ranked = sorted(papers, key=lambda x: x['relevance_score'], reverse=True)
    
    print(f"  Top 5 after ranking:")
    for p in ranked[:5]:
        print(f"    [{p['relevance_score']:.3f}] {p['title'][:60]}...")
    
    return ranked[:top_k]


# ============================================================
# 4. LLM RELEVANCE FILTER
# ============================================================

class PaperRelevance(BaseModel):
    """Relevance assessment for a single paper."""
    is_relevant: bool = Field(description="Whether this paper is relevant to answering the question")
    reason: str = Field(description="Brief reason for the relevance decision")


def filter_by_llm_relevance(papers: List[Dict], user_query: str, max_papers: int = 10) -> List[Dict]:
    """
    Use LLM to filter papers based on actual relevance to the question.
    This is the final, precise filtering step.
    """
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
                print(f"  ✓ {paper['title'][:50]}... - {result.reason[:50]}")
            else:
                print(f"  ✗ {paper['title'][:50]}...")
            
            if len(relevant_papers) >= max_papers:
                break
                
        except Exception as e:
            print(f"  Error evaluating paper: {e}")
            relevant_papers.append(paper)  # Include on error
    
    print(f"  Filtered to {len(relevant_papers)} relevant papers")
    return relevant_papers


# ============================================================
# MAIN RETRIEVAL FUNCTION
# ============================================================

def enhanced_retrieval(user_query: str, max_final_papers: int = 10) -> List[Dict]:
    """
    Full enhanced retrieval pipeline:
    1. Optimize query
    2. Search multiple sources
    3. Deduplicate
    4. Rank by relevance
    5. LLM filter
    """
    print(f"\n{'='*60}")
    print(f"ENHANCED RETRIEVAL: {user_query}")
    print(f"{'='*60}\n")
    
    # 1. Optimize query
    optimized = optimize_query(user_query)
    
    # 2. Multi-source retrieval
    # Primary PubMed search with optimized query
    pubmed_papers = search_pubmed(optimized.pubmed_query, max_results=50)
    
    # Secondary PubMed search with key concepts (catches different papers)
    concept_query = " AND ".join(optimized.key_concepts[:3])
    pubmed_papers_2 = search_pubmed(concept_query, max_results=30)
    
    # Semantic Scholar search
    semantic_papers = search_semantic_scholar(optimized.semantic_query, max_results=50)
    
    all_papers = pubmed_papers + pubmed_papers_2 + semantic_papers
    print(f"\n---TOTAL CANDIDATES: {len(all_papers)}---")
    
    if not all_papers:
        return []
    
    # 3. Deduplicate
    unique_papers = deduplicate_papers(all_papers)
    print(f"---AFTER DEDUP: {len(unique_papers)}---")
    
    # 4. Rank by relevance (embedding-based)
    ranked_papers = rank_by_relevance(unique_papers, user_query, top_k=20)
    
    # 5. LLM filter for final selection
    final_papers = filter_by_llm_relevance(ranked_papers, user_query, max_papers=max_final_papers)
    
    print(f"\n---FINAL PAPERS: {len(final_papers)}---")
    for i, p in enumerate(final_papers, 1):
        print(f"  {i}. [{p['year']}] {p['title'][:60]}...")
        print(f"     Source: {p['source']}, Citations: {p['citation_count']}, PMID: {p.get('pmid', 'N/A')}")
    
    return final_papers


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    query = "What are the benefits of sleeping 7-8 hours?"
    papers = enhanced_retrieval(query, max_final_papers=8)
    
    print(f"\n\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    for i, p in enumerate(papers, 1):
        print(f"\n{i}. {p['title']}")
        print(f"   Journal: {p['journal']} ({p['year']})")
        print(f"   PMID: {p.get('pmid', 'N/A')}")
        print(f"   Citations: {p['citation_count']}")
        print(f"   Relevance: {p.get('relevance_reason', 'N/A')}")
