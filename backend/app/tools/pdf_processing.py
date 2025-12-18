import os
import re
from pdf2image import convert_from_path
from pypdf import PdfReader
from app.tools.vision import analyze_chart
from app.services.ingestion import ingest_paper_batch  
import weaviate

os.makedirs("static/figures", exist_ok=True)

def process_pdf(pdf_path: str, paper_title: str):
    print(f"Processing PDF for Visuals: {pdf_path}")

    try:
        reader = PdfReader(pdf_path)
        visual_pages = convert_from_path(pdf_path)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return
    
    id_match = re.search(r'ID: (\d+)', paper_title)
    safe_prefix = id_match.group(1) if id_match else paper_title.replace(' ', '_').replace(':', '').replace('/', '')

    extracted_data = []
    
    num_pages = min(len(reader.pages), len(visual_pages))

    for i in range(num_pages):
        pypdf_page = reader.pages[i]
        
        if len(pypdf_page.images) > 0:
            target_image = visual_pages[i]
            
            try:
                description = analyze_chart(target_image)
                
                image_filename = f"{safe_prefix}_page_{i+1}.jpg"
                save_path = f"static/figures/{image_filename}"
                
                target_image.save(save_path, "JPEG")

                extracted_data.append({
                    "title": f"Figure from {paper_title} (Page {i+1})",
                    "abstract": f"**Visual Analysis:** {description}",
                    "journal": "Visual Data", 
                    "year": 2025,
                    "source_id": f"IMG_{image_filename}"
                })
            except Exception as e:
                print(f"Failed to analyze page {i+1}: {e}")
        else:
            print(f"Skipping Page {i+1} (Text only, saving cost)")

    if extracted_data:
        ingest_paper_batch(extracted_data)
        print(f"Ingested {len(extracted_data)} visual insights.")
    else:
        print("No significant visuals found in this paper.")