"""
Pytest fixtures and configuration for backend tests.

Provides reusable fixtures for testing API endpoints, services, and utilities.
"""
import os
import sys
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session", autouse=True)
def set_test_environment():
    """Set environment variables for testing."""
    os.environ["OPENAI_API_KEY"] = "test-key-not-real"
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"
    yield


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch("langchain_openai.ChatOpenAI") as mock_chat:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content="Test response")
        mock_chat.return_value = mock_instance
        yield mock_chat


@pytest.fixture
def mock_embeddings():
    """Mock OpenAI embeddings."""
    with patch("langchain_openai.OpenAIEmbeddings") as mock_embed:
        mock_instance = MagicMock()
        mock_instance.embed_documents.return_value = [[0.1] * 1536]
        mock_instance.embed_query.return_value = [0.1] * 1536
        mock_embed.return_value = mock_instance
        yield mock_embed


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    with patch("redis.from_url") as mock:
        mock_client = MagicMock()
        mock_client.ping.side_effect = Exception("Redis not available")
        mock.return_value = mock_client
        yield mock


@pytest.fixture
def sample_paper():
    """Sample paper data for testing."""
    return {
        "title": "Rapamycin extends lifespan in mice",
        "abstract": "This study demonstrates that rapamycin significantly extends lifespan in middle-aged mice through mTOR inhibition.",
        "journal": "Nature",
        "year": 2023,
        "pmid": "12345678",
        "doi": "10.1234/nature.2023",
        "citation_count": 150,
        "source": "pubmed",
        "url": "https://pubmed.ncbi.nlm.nih.gov/12345678"
    }


@pytest.fixture
def sample_papers(sample_paper):
    """List of sample papers for testing."""
    papers = [sample_paper.copy() for _ in range(5)]
    for i, paper in enumerate(papers):
        paper["title"] = f"Research paper {i+1}"
        paper["pmid"] = f"{12345670 + i}"
        paper["citation_count"] = 100 - (i * 10)
    return papers


@pytest.fixture
def sample_report():
    """Sample research report for testing."""
    return {
        "id": "test-report-123",
        "question": "What are the effects of rapamycin on longevity?",
        "generated_at": "2024-01-15T10:30:00Z",
        "executive_summary": "Rapamycin has shown promising effects on longevity in multiple studies.",
        "key_findings": [
            {
                "statement": "Rapamycin extends lifespan by 10-15% in mice",
                "source_indices": [1, 2],
                "confidence": "high"
            }
        ],
        "detailed_analysis": "The research indicates...",
        "protocols": [
            {
                "name": "Low-dose rapamycin protocol",
                "species": "Human",
                "dosage": "1mg weekly",
                "frequency": "Once weekly",
                "duration": "12 months",
                "result": "Improved immune function",
                "source_index": 1
            }
        ],
        "limitations": "Most studies are in animal models.",
        "sources": [],
        "total_papers_searched": 100,
        "papers_used": 10
    }


@pytest.fixture
def test_client():
    """Create a test client for API testing."""
    # Import here to avoid circular imports
    from app.main import app
    
    with TestClient(app) as client:
        yield client
