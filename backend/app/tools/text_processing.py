
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.ingestion import ingest_paper_batch
import os

def ingest_full_text(pdf_path: str, pmid: str, title:str):
    """
    1. Reads PDF text page by page
    2. Splits text into overlapping chunks
    3. Ingests into Weaviate
    """
    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return
    
    full_text = ""
    chunks_to_ingest = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n\n"

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    chunks = text_splitter.split_text(full_text)
    print(f"   ✂️ Split into {len(chunks)} chunks.")

    for i, chunk in enumerate(chunks):
        chunks_to_ingest.append({
            "title": f"{title} (Chunk {i+1})",
            "abstract": chunk,
            "journal": "Full Text Data",
            "year": 2025,
            "source_id": f"{pmid}_text_{i}"
        })
    
    if chunks_to_ingest:
        ingest_paper_batch(chunks_to_ingest)
    else:
        print("No text chunks to ingest")