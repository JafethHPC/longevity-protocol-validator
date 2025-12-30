"""
Full-Text PDF Service

Downloads and extracts full text from open access PDFs.
Uses multiple sources: Unpaywall API, PMC Open Access.
"""
import requests
from typing import Optional, Dict, Tuple
from io import BytesIO
import re

from pypdf import PdfReader

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FullTextService:
    """Service for retrieving and extracting full-text from open access papers."""
    
    UNPAYWALL_BASE = "https://api.unpaywall.org/v2"
    PMC_OA_BASE = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"
    PMC_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, email: Optional[str] = None):
        self.email = email or settings.API_CONTACT_EMAIL
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"LongevityValidator/1.0 (mailto:{self.email})"
        })
    
    def get_full_text(self, pmid: str = None, doi: str = None, pmcid: str = None) -> Optional[Dict]:
        """
        Attempt to get full text for a paper using available identifiers.
        
        Returns:
            Dict with keys: 'text', 'source', 'word_count' or None if not available
        """
        if not any([pmid, doi, pmcid]):
            return None
        
        full_text = None
        source = None
        
        if pmcid:
            full_text = self._get_pmc_fulltext(pmcid)
            if full_text:
                source = "PMC"
        
        if not full_text and pmid:
            pmcid = self._pmid_to_pmcid(pmid)
            if pmcid:
                full_text = self._get_pmc_fulltext(pmcid)
                if full_text:
                    source = "PMC"
        
        if not full_text and doi:
            full_text = self._get_unpaywall_fulltext(doi)
            if full_text:
                source = "Unpaywall"
        
        if not full_text and pmid:
            doi = self._pmid_to_doi(pmid)
            if doi:
                full_text = self._get_unpaywall_fulltext(doi)
                if full_text:
                    source = "Unpaywall"
        
        if full_text:
            cleaned = self._clean_text(full_text)
            return {
                "text": cleaned,
                "source": source,
                "word_count": len(cleaned.split()),
                "char_count": len(cleaned)
            }
        
        return None
    
    def _pmid_to_pmcid(self, pmid: str) -> Optional[str]:
        """Convert PMID to PMCID using ID converter."""
        try:
            url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pmid}&format=json"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                records = data.get("records", [])
                if records and "pmcid" in records[0]:
                    return records[0]["pmcid"]
        except Exception as e:
            logger.debug(f"PMID->PMCID conversion failed: {e}")
        return None
    
    def _pmid_to_doi(self, pmid: str) -> Optional[str]:
        """Get DOI from PMID using E-utilities."""
        try:
            url = f"{self.PMC_BASE}/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                if pmid in result:
                    article_ids = result[pmid].get("articleids", [])
                    for aid in article_ids:
                        if aid.get("idtype") == "doi":
                            return aid.get("value")
        except Exception as e:
            logger.debug(f"PMID->DOI conversion failed: {e}")
        return None
    
    def _get_pmc_fulltext(self, pmcid: str) -> Optional[str]:
        """Get full text from PMC Open Access."""
        try:
            pmcid_clean = pmcid.replace("PMC", "")
            url = f"{self.PMC_OA_BASE}?id=PMC{pmcid_clean}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return None
            
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)
            
            records = root.findall(".//record")
            if not records:
                return None
            
            for record in records:
                pdf_link = None
                for link in record.findall(".//link"):
                    format_type = link.get("format", "")
                    if format_type == "pdf":
                        href = link.get("href")
                        if href:
                            pdf_link = href
                            break
                
                if pdf_link:
                    return self._download_and_extract_pdf(pdf_link)
            
            return None
            
        except Exception as e:
            logger.debug(f"PMC full text retrieval failed for {pmcid}: {e}")
            return None
    
    def _get_unpaywall_fulltext(self, doi: str) -> Optional[str]:
        """Get full text PDF via Unpaywall API."""
        try:
            url = f"{self.UNPAYWALL_BASE}/{doi}?email={self.email}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if not data.get("is_oa"):
                return None
            
            best_loc = data.get("best_oa_location", {})
            pdf_url = best_loc.get("url_for_pdf")
            
            if not pdf_url:
                for loc in data.get("oa_locations", []):
                    if loc.get("url_for_pdf"):
                        pdf_url = loc["url_for_pdf"]
                        break
            
            if pdf_url:
                return self._download_and_extract_pdf(pdf_url)
            
            return None
            
        except Exception as e:
            logger.debug(f"Unpaywall retrieval failed for {doi}: {e}")
            return None
    
    def _download_and_extract_pdf(self, pdf_url: str) -> Optional[str]:
        """Download PDF and extract text."""
        try:
            response = self.session.get(
                pdf_url, 
                timeout=30,
                headers={"Accept": "application/pdf"},
                stream=True
            )
            
            if response.status_code != 200:
                return None
            
            content_type = response.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower() and not pdf_url.endswith(".pdf"):
                return None
            
            pdf_bytes = BytesIO(response.content)
            reader = PdfReader(pdf_bytes)
            
            text_parts = []
            for page in reader.pages[:50]:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            if not text_parts:
                return None
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.debug(f"PDF extraction failed from {pdf_url[:50]}...: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        text = re.sub(r'\s+', ' ', text)
        
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        
        text = re.sub(r'\[?\d+\]?[\s,]+(?=\[?\d+\]?)', '', text)
        
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 20:
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines).strip()
    
    def get_abstract_and_fulltext(
        self, 
        abstract: str, 
        pmid: str = None, 
        doi: str = None,
        pmcid: str = None,
        max_fulltext_chars: int = 15000
    ) -> Tuple[str, bool]:
        """
        Get combined abstract and full text for paper context.
        
        Returns:
            Tuple of (combined_text, has_fulltext)
        """
        full_text_result = self.get_full_text(pmid=pmid, doi=doi, pmcid=pmcid)
        
        if full_text_result and full_text_result["char_count"] > len(abstract or ""):
            full_text = full_text_result["text"]
            
            if len(full_text) > max_fulltext_chars:
                intro_end = full_text.find("Methods", 0, 3000)
                if intro_end == -1:
                    intro_end = min(3000, len(full_text) // 4)
                
                discussion_start = max(
                    full_text.rfind("Discussion"),
                    full_text.rfind("Conclusion"),
                    full_text.rfind("Results")
                )
                
                if discussion_start > intro_end:
                    intro = full_text[:intro_end]
                    discussion = full_text[discussion_start:]
                    
                    remaining = max_fulltext_chars - len(intro) - len(discussion)
                    if remaining > 0:
                        mid_start = intro_end
                        mid_end = min(mid_start + remaining, discussion_start)
                        middle = full_text[mid_start:mid_end]
                        full_text = intro + "\n\n[...]\n\n" + middle + "\n\n[...]\n\n" + discussion
                    else:
                        full_text = intro + "\n\n[...]\n\n" + discussion
                else:
                    full_text = full_text[:max_fulltext_chars] + "\n\n[truncated]"
            
            return full_text, True
        
        return abstract or "", False


fulltext_service = FullTextService()
