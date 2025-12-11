import os
from pdf2image import convert_from_path
from app.vision import analyze_chart
from app.ingestion import ingest_paper_batch  
import weaviate

os.makedirs("static/figures", exist_ok=True)

def process_pdf(pdf_path: str, paper_title: str):
    """
    1. Convert PDF pages to images/
    2. (Simplification) Treat each page as an image to find charts
    3. Analyze with GPT-4o.
    4. Ingest into Weaviate.
    """
    print("Processing PDF...")

    try:
        pages = convert_from_path(pdf_path)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return
    
    extracted_data = []

    for i, page in enumerate(pages[:]):
        description = analyze_chart(page)

        image_filename = f"{paper_title.replace(' ', '_')}_page_{i+1}.jpg"
        save_path = f"static/figures/{image_filename}"
        page.save(save_path, "JPEG")

        extracted_data.append({
            "title": f"Figure from {paper_title} (Page {i+1})",
            "abstract": f"**Visual Analysis:** {description}",
            "journal": "Visual Data", 
            "year": 2025,
            "source_id": f"IMG_{image_filename}"
        })

    if extracted_data:
        ingest_paper_batch(extracted_data)

if __name__ == "__main__":
    process_pdf("rapamycin.pdf", "Rapamycin Study")