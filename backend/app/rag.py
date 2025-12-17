from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import List
from app.core.config import settings
from app.core.db import get_weaviate_client
from flashrank import Ranker, RerankRequest

class ProtocolMetrics(BaseModel):
    """
    Structured extraction of a specific scientific protocol found in the papers.
    """
    protocol_name: str = Field(description="Name of the intervention/drug (e.g. 'Rapamycin', '17-alpha-estradiol')")
    species: str = Field(description="Species used in the study (e.g., 'C57BL/6 Mouse', 'Human', 'Wistar Rat')")
    dosage_amount: str = Field(description="Precise dosage used (e.g., '14 ppm', '5 mg/kg', '1000 mg')")
    administration_route: str = Field(description="Route of administration (e.g., 'Oral', 'Intraperitoneal Injection', 'Dietary')")
    sample_size: int = Field(description="Number of subjects in the study (N-value). Use 0 if not explicitly mentioned.")
    outcome_summary: str = Field(description="Brief summary of the outcome (e.g., 'Median lifespan increased by 14%')")

class ResearchIngestion(BaseModel):
    """
    Structured response for scientific papers
    """
    answer_summary: str = Field(..., description="A direct, 2-3 sentence answer to the user's question")
    consensus_points: List[str] = Field(..., description="List of facts that appear to be agreed upon across multiple papers.")
    conflict_points: List[str] = Field(..., description="List of points where papers disagree or where results are inconclusive/contradictory.")
    limitations: str = Field(..., description="A note on what is NOT known or if the papers focus on specific groups (e.g., transplant patients, mice, etc.)")
    extracted_protocols: List[ProtocolMetrics] = Field(default_factory=list, description="List of specific protocols identified in the papers.")
    
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=settings.OPENAI_API_KEY
).with_structured_output(ResearchIngestion)

template = """You are an expert Biologist and Longevity Researcher.
Analyze the provided context papers to answer the user's question.

Your goal is to:
1. Identify consensus and conflicts.
2. EXTRACT PRECISE DATA into the 'extracted_protocols' list. 
   - Look for specific N-values (sample sizes), precise dosages (e.g. '5mg/kg', not 'high dose'), and outcomes.
   - If a paper mentions multiple protocols (e.g. Low Dose vs High Dose), extract them as separate entries.
3. Summarize limitations.

Context: {context}

Question: {question}

Answer: """

prompt = ChatPromptTemplate.from_template(template)
ranker = Ranker() 

def get_context(query:str):
    """
    Retrieves the raw text chunks from Weaviate to feed into the AI.
    Uses Two-Stage Retrieval:
    1. Vector Search (Broad): Fetch top 50 chunks
    2. Reranking (precise): Filter for top 10 chunks using Cross-Encoder
    """
    client = get_weaviate_client()

    try:
        papers = client.collections.get("Paper")
        response = papers.query.near_text(
            query=query,
            limit=50
        )
        
        if not response.objects:
            return ""

        passages = []
        for idx, obj in enumerate(response.objects):
            passages.append({
                "id": idx,
                "text": obj.properties.get('abstract', ''),
                "meta": obj.properties
            })

        rerank_request = RerankRequest(query=query, passages=passages)
        reranked_results = ranker.rerank(rerank_request)
        
        top_results = reranked_results[:10]

        context_str = "\n\n".join([
            f"Paper: {res['meta']['title']}\nSource: {res['meta']['source_id']}\nAbstract: {res['text']}"
            for res in top_results
        ])
        
        return context_str
    
    except Exception as e:
        print(f"Error getting context: {e}")
        return ""

    finally: 
        client.close()


    