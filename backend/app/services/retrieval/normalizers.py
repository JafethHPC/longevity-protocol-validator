"""
Clinical trial normalization utilities.

Converts clinical trial records to the standard paper format
so they can be processed alongside research papers.
"""
from typing import Dict


def normalize_trial_to_paper(trial: Dict) -> Dict:
    """
    Convert a clinical trial record to the standard paper format.
    
    This allows clinical trials to be processed alongside research papers
    in the rest of the pipeline (ranking, filtering, display).
    
    Args:
        trial: Raw clinical trial record from ClinicalTrials.gov
        
    Returns:
        Dict formatted like a research paper with trial-specific metadata
    """
    # Build a comprehensive abstract from trial data
    abstract_parts = []
    
    if trial.get('abstract'):
        abstract_parts.append(trial['abstract'])
    
    if trial.get('conditions'):
        abstract_parts.append(f"Conditions: {', '.join(trial['conditions'][:3])}")
    
    if trial.get('interventions'):
        abstract_parts.append(f"Interventions: {', '.join(trial['interventions'][:3])}")
    
    if trial.get('primary_outcomes'):
        abstract_parts.append(f"Primary outcomes: {', '.join(trial['primary_outcomes'][:2])}")
    
    if trial.get('enrollment'):
        abstract_parts.append(f"Enrollment: {trial['enrollment']} participants")
    
    if trial.get('phase') and trial['phase'] != 'N/A':
        abstract_parts.append(f"Phase: {trial['phase']}")
    
    abstract = " | ".join(abstract_parts) if abstract_parts else trial.get('title', '')
    
    return {
        'title': trial.get('title', ''),
        'abstract': abstract,
        'journal': 'ClinicalTrials.gov',
        'year': trial.get('year', 0) or 2024,
        'pmid': trial.get('nct_id', ''),  # Use NCT ID as identifier
        'doi': '',
        'source': 'ClinicalTrials.gov',
        'is_review': False,
        'citation_count': 0,  # Trials don't have citations
        'url': trial.get('url', ''),
        'type': 'clinical_trial',
        'status': trial.get('status', ''),
        'phase': trial.get('phase', ''),
        'has_results': trial.get('has_results', False),
        'conditions': trial.get('conditions', []),
        'interventions': trial.get('interventions', []),
    }
