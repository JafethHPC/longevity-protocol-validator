"""
ClinicalTrials.gov API v2.0 data source.

Provides access to 400k+ clinical trials with:
- Modern REST API with JSON responses
- Structured fields (enums, ISO dates)
- No authentication required
- Rate limit: ~50 requests/minute

API Documentation: https://clinicaltrials.gov/data-api/api
"""
from typing import List, Dict, Optional
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

BASE_URL = "https://clinicaltrials.gov/api/v2"

# Fields to retrieve for each study
DEFAULT_FIELDS = [
    "NCTId",
    "BriefTitle",
    "OfficialTitle",
    "BriefSummary",
    "Condition",
    "InterventionName",
    "InterventionType",
    "Phase",
    "OverallStatus",
    "StartDate",
    "CompletionDate",
    "EnrollmentCount",
    "StudyType",
    "PrimaryOutcomeMeasure",
    "SecondaryOutcomeMeasure",
    "EligibilityCriteria",
    "LeadSponsorName",
    "HasResults"
]

_executor = ThreadPoolExecutor(max_workers=2)


def _search_trials_sync(
    query: str,
    max_results: int = 50,
    status: Optional[str] = None,
    phase: Optional[str] = None,
    has_results: Optional[bool] = None
) -> List[Dict]:
    """
    Synchronous search implementation for ClinicalTrials.gov.
    
    Args:
        query: Search terms (condition, intervention, etc.)
        max_results: Maximum number of trials to return
        status: Filter by status (RECRUITING, COMPLETED, etc.)
        phase: Filter by phase (PHASE1, PHASE2, PHASE3, PHASE4)
        has_results: Only return trials with posted results
    """
    print(f"---SEARCHING CLINICALTRIALS.GOV: {query[:50]}...---")
    
    params = {
        "query.term": query,
        "pageSize": min(max_results, 100),  # API max is 100 per page
        "fields": ",".join(DEFAULT_FIELDS),
        "sort": "LastUpdatePostDate:desc"  # Most recently updated first
    }
    
    # Add optional filters
    if status:
        params["filter.overallStatus"] = status
    if phase:
        params["filter.advanced"] = f"AREA[Phase]{phase}"
    if has_results:
        params["filter.advanced"] = "AREA[HasResults]true"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(
            f"{BASE_URL}/studies", 
            params=params, 
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 429:
            print("  Rate limited, waiting 2 seconds...")
            time.sleep(2)
            response = requests.get(
                f"{BASE_URL}/studies", 
                params=params, 
                headers=headers,
                timeout=30
            )
        
        if response.status_code != 200:
            print(f"  Error: {response.status_code}")
            return []
        
        data = response.json()
        trials = []
        
        for study in data.get("studies", []):
            try:
                trial = _normalize_trial(study)
                if trial:
                    trials.append(trial)
            except Exception as e:
                print(f"  Error parsing trial: {e}")
                continue
        
        print(f"  Found {len(trials)} clinical trials")
        return trials
        
    except requests.exceptions.Timeout:
        print("  ClinicalTrials.gov timeout")
        return []
    except Exception as e:
        print(f"  ClinicalTrials.gov error: {e}")
        return []


def _normalize_trial(study: Dict) -> Optional[Dict]:
    """Convert API response to standard format."""
    protocol = study.get("protocolSection", {})
    
    # Identification
    id_module = protocol.get("identificationModule", {})
    nct_id = id_module.get("nctId", "")
    
    if not nct_id:
        return None
    
    # Status
    status_module = protocol.get("statusModule", {})
    
    # Design
    design_module = protocol.get("designModule", {})
    
    # Description
    desc_module = protocol.get("descriptionModule", {})
    brief_summary = desc_module.get("briefSummary", "")
    
    # Conditions
    conditions_module = protocol.get("conditionsModule", {})
    conditions = conditions_module.get("conditions", [])
    
    # Interventions
    arms_module = protocol.get("armsInterventionsModule", {})
    interventions = arms_module.get("interventions", [])
    intervention_names = [i.get("name", "") for i in interventions]
    intervention_types = [i.get("type", "") for i in interventions]
    
    # Outcomes
    outcomes_module = protocol.get("outcomesModule", {})
    primary_outcomes = outcomes_module.get("primaryOutcomes", [])
    primary_measures = [o.get("measure", "") for o in primary_outcomes]
    
    # Eligibility
    eligibility_module = protocol.get("eligibilityModule", {})
    eligibility_criteria = eligibility_module.get("eligibilityCriteria", "")
    
    # Sponsor
    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
    lead_sponsor = sponsor_module.get("leadSponsor", {})
    sponsor_name = lead_sponsor.get("name", "")
    
    # Parse dates
    start_date = status_module.get("startDateStruct", {}).get("date", "")
    completion_date = status_module.get("completionDateStruct", {}).get("date", "")
    
    # Extract year from start date
    year = 0
    if start_date:
        try:
            year = int(start_date.split("-")[0])
        except:
            pass
    
    # Phases
    phases = design_module.get("phases", [])
    phase_str = ", ".join(phases) if phases else "N/A"
    
    # Has results?
    has_results = study.get("hasResults", False)
    
    return {
        "nct_id": nct_id,
        "title": id_module.get("briefTitle", ""),
        "official_title": id_module.get("officialTitle", ""),
        "abstract": brief_summary,  # Use brief summary as abstract equivalent
        "status": status_module.get("overallStatus", ""),
        "phase": phase_str,
        "conditions": conditions,
        "interventions": intervention_names,
        "intervention_types": intervention_types,
        "primary_outcomes": primary_measures,
        "eligibility_criteria": eligibility_criteria[:500] if eligibility_criteria else "",
        "enrollment": design_module.get("enrollmentInfo", {}).get("count", 0),
        "sponsor": sponsor_name,
        "start_date": start_date,
        "completion_date": completion_date,
        "has_results": has_results,
        "year": year,
        "url": f"https://clinicaltrials.gov/study/{nct_id}",
        "source": "ClinicalTrials.gov",
        "type": "clinical_trial"
    }


async def search_clinical_trials(
    query: str,
    max_results: int = 50,
    status: Optional[str] = None,
    phase: Optional[str] = None,
    has_results: Optional[bool] = None
) -> List[Dict]:
    """
    Async wrapper for clinical trial search.
    
    Args:
        query: Search terms (condition, intervention, etc.)
        max_results: Maximum number of trials to return
        status: Filter by status - options:
            - RECRUITING
            - COMPLETED
            - ACTIVE_NOT_RECRUITING
            - NOT_YET_RECRUITING
            - TERMINATED
            - WITHDRAWN
        phase: Filter by phase - options:
            - PHASE1
            - PHASE2
            - PHASE3
            - PHASE4
            - EARLY_PHASE1
        has_results: Only return trials with posted results
    
    Returns:
        List of clinical trial dictionaries
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor,
        _search_trials_sync,
        query,
        max_results,
        status,
        phase,
        has_results
    )


async def get_trial_by_nct_id(nct_id: str) -> Optional[Dict]:
    """
    Get a specific trial by its NCT ID.
    
    Args:
        nct_id: The NCT identifier (e.g., "NCT12345678")
    
    Returns:
        Trial dictionary or None if not found
    """
    def _fetch_sync():
        print(f"---FETCHING TRIAL: {nct_id}---")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            response = requests.get(
                f"{BASE_URL}/studies/{nct_id}",
                params={"fields": ",".join(DEFAULT_FIELDS)},
                headers=headers,
                timeout=15
            )
            
            if response.status_code != 200:
                print(f"  Error: {response.status_code}")
                return None
            
            data = response.json()
            return _normalize_trial(data)
            
        except Exception as e:
            print(f"  Error fetching {nct_id}: {e}")
            return None
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _fetch_sync)


async def search_trials_with_results(
    condition: str,
    intervention: Optional[str] = None,
    max_results: int = 25
) -> List[Dict]:
    """
    Search specifically for completed trials with posted results.
    
    These are the most useful for evidence-based analysis since
    they contain actual outcome data.
    """
    query_parts = [condition]
    if intervention:
        query_parts.append(intervention)
    
    query = " ".join(query_parts)
    
    return await search_clinical_trials(
        query=query,
        max_results=max_results,
        status="COMPLETED",
        has_results=True
    )
