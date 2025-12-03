from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings
import weaviate
import weaviate.classes.query as wcq

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=settings.OPENAI_API_KEY
)

template = """You are an expert Biologist and Longevity Researcher.
Answer the user's question based ONLY on the the following content of papers(scientific papers).

Rules:
1. If the papers list adverse events, side effects, or toxicity for specific groups (e.g., transplant patients, mice, etc.), cite them explicitly.
2. Do not use outside knowledge.
3. If the answer is completely absent, say "I cannot find evidence in the provided papers."

Context: {context}

Question: {question}

Answer: """

prompt = ChatPromptTemplate.from_template(template)

def get_context(query:str):
    """
    Retrieves the raw text chunks from Weaviate to feed into the AI.
    """
    client = weaviate.connect_to_local(
        headers={
            "X-OpenAI-Api-Key": settings.OPENAI_API_KEY
        }
    )

    try:
        papers = client.collections.get("Paper")
        response = papers.query.near_text(
            query=query,
            limit=10
        )

        context_str = "\n\n".join([
            f"Paper: {paper.properties['title']}\nAbstract: {paper.properties['abstract']}"
            for paper in response.objects
        ])

        return context_str

    except Exception as e:
        print(f"Error getting context: {e}")
        return ""

    finally: 
        client.close()

def generate_answer(query: str):
    """
    Generates an answer to the user's question based on the context.

    The full RAG Chain:
    1. Get Context (Weaviate)
    2. Format Prompt
    3. Send to GPT-4o
    """
    context_text = get_context(query)

    formatted_prompt = prompt.format(
        context=context_text,
        question=query
    )

    response = llm.invoke(formatted_prompt)

    return {
        "answer": response.content,
        "context_used": context_text
    }
    