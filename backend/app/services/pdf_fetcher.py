import requests
import os
import xml.etree.ElementTree as ET
from Bio import Entrez
import time

Entrez.email = "your_email@example.com"

def get_pmc_id(pmid: str) -> str:
    """
    Converts a standard PubMed ID (PMID) to a PubMed Central ID (PMCID).
    Only PMC papers have free full-text PDFs.
    """
    time.sleep(1)
    print(f"Converting PMID: {pmid} to PMCID...")
    try:
        handle = Entrez.elink(dbfrom="pubmed", db="pmc", linkname="pubmed_pmc", id=pmid)
        results = Entrez.read(handle)
        handle.close()

        if not results or not results[0]["LinkSetDb"]:
            return None

        pmc_id = results[0]["LinkSetDb"][0]["Link"][0]["Id"]
        return f"PMC{pmc_id}"
    except Exception as e:
        print(f"Error getting PMC ID: {e}")
        return None

def get_oa_pdf_url(pmc_id: str) -> str:
    """
    Queries the PMC Open Access Web Service to get the direct PDF URL.
    This bypasses the interactive "Proof of Work" challenge on the main website.
    """
    url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmc_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for link in root.findall(".//link"):
                if link.get("format") == "pdf":
                    href = link.get("href")
                    if href.startswith("ftp://"):
                        href = href.replace("ftp://", "https://")
                    return href
    except Exception as e:
        print(f"Error fetching OA URL: {e}")
    return None

def download_pdf(pmc_id: str, save_path: str):
    """
    Downloads the PDF using the OA API if available, otherwise falls back to web scraping.
    """
    pdf_url = get_oa_pdf_url(pmc_id)
    
    if not pdf_url:
        print(f"No Open Access PDF found via API for {pmc_id}. Trying web scraping fallback...")
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/main.pdf"
    
    print(f"Downloading PDF from: {pdf_url}")

    headers = {
            "User-Agent": "LongevityValidatorBot/1.0 (mailto:your_email@example.com)",
            "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://pubmed.ncbi.nlm.nih.gov/",
            "Connection": "keep-alive"
    }

    try:
        response = requests.get(pdf_url, headers=headers, stream=True)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "").lower()
            
            if "pdf" not in content_type and "application/octet-stream" not in content_type:
                print(f"Invalid Content-Type: {content_type}. This is likely a bot challenge page.")
                return False

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Download Complete")
            return True
        else:
            print(f"Failed to download PDF. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return False