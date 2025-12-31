"""Tests for services/retrieval/ - Retrieval pipeline modules."""
from unittest.mock import patch, MagicMock

import pytest


class TestRetrievalTypes:
    """Test the retrieval types module."""

    def test_progress_callback_type_exists(self):
        """ProgressCallback type should be importable."""
        from app.services.retrieval.types import ProgressCallback
        
        assert ProgressCallback is not None

    def test_noop_callback_exists(self):
        """_noop_callback should be importable."""
        from app.services.retrieval.types import _noop_callback
        
        # Should not raise when called
        _noop_callback("step", "message", "detail")

    def test_constants_defined(self):
        """Constants should be defined."""
        from app.services.retrieval.types import (
            MAX_CONCURRENT_LLM_CALLS,
            BATCH_SIZE
        )
        
        assert isinstance(MAX_CONCURRENT_LLM_CALLS, int)
        assert isinstance(BATCH_SIZE, int)
        assert MAX_CONCURRENT_LLM_CALLS > 0
        assert BATCH_SIZE > 0


class TestNormalizers:
    """Test the normalizers module."""

    def test_normalize_trial_to_paper(self):
        """normalize_trial_to_paper should convert trial to paper format."""
        from app.services.retrieval.normalizers import normalize_trial_to_paper
        
        trial = {
            "nct_id": "NCT12345678",
            "title": "Test Trial",
            "abstract": "A test clinical trial",
            "status": "Completed",
            "phase": "Phase 3",
            "conditions": ["Diabetes"],
            "interventions": ["Test Drug"],
            "year": 2023,
            "enrollment": 100,
            "has_results": True,
            "url": "https://clinicaltrials.gov/ct2/show/NCT12345678"
        }
        
        paper = normalize_trial_to_paper(trial)
        
        assert paper is not None
        assert "title" in paper
        assert "abstract" in paper
        assert paper["source"] == "ClinicalTrials.gov"
        assert paper["type"] == "clinical_trial"

    def test_normalize_trial_handles_missing_fields(self):
        """Should handle trials with missing optional fields."""
        from app.services.retrieval.normalizers import normalize_trial_to_paper
        
        trial = {
            "nct_id": "NCT12345678",
            "title": "Minimal Trial"
        }
        
        paper = normalize_trial_to_paper(trial)
        
        assert paper is not None
        assert paper["title"] == "Minimal Trial"
        assert paper["pmid"] == "NCT12345678"


class TestRanking:
    """Test the ranking module."""

    def test_deduplicate_papers_removes_exact_duplicates(self, sample_papers):
        """deduplicate_papers should remove exact duplicates."""
        from app.services.retrieval.ranking import deduplicate_papers
        
        # Add a duplicate
        papers = sample_papers + [sample_papers[0].copy()]
        
        result = deduplicate_papers(papers)
        
        # Should have one less paper
        assert len(result) < len(papers)

    def test_deduplicate_papers_preserves_unique(self, sample_papers):
        """deduplicate_papers should preserve unique papers."""
        from app.services.retrieval.ranking import deduplicate_papers
        
        result = deduplicate_papers(sample_papers)
        
        assert len(result) == len(sample_papers)


class TestRetrievalPackageExports:
    """Test that the retrieval package exports correctly."""

    def test_enhanced_retrieval_is_exported(self):
        """enhanced_retrieval should be importable from package."""
        from app.services.retrieval import enhanced_retrieval
        
        assert callable(enhanced_retrieval)

    def test_progress_callback_is_exported(self):
        """ProgressCallback should be importable from package."""
        from app.services.retrieval import ProgressCallback
        
        assert ProgressCallback is not None

    def test_deduplicate_papers_is_exported(self):
        """deduplicate_papers should be importable from package."""
        from app.services.retrieval import deduplicate_papers
        
        assert callable(deduplicate_papers)
