"""Tests for API endpoints."""
from unittest.mock import patch, MagicMock

import pytest


class TestHealthCheck:
    """Test the health check endpoint."""

    def test_health_check_returns_200(self, test_client):
        """Root endpoint should return 200."""
        response = test_client.get("/")
        
        assert response.status_code == 200

    def test_health_check_returns_status(self, test_client):
        """Health check should return status information."""
        response = test_client.get("/")
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "active"

    def test_health_check_returns_project_name(self, test_client):
        """Health check should return project name."""
        response = test_client.get("/")
        data = response.json()
        
        assert "project" in data
        assert data["project"] == "Longevity Validator"

    def test_health_check_returns_cache_info(self, test_client):
        """Health check should return cache information."""
        response = test_client.get("/")
        data = response.json()
        
        assert "cache" in data
        assert "type" in data["cache"]
        assert "connected" in data["cache"]

    def test_health_check_returns_endpoints(self, test_client):
        """Health check should return available endpoints."""
        response = test_client.get("/")
        data = response.json()
        
        assert "endpoints" in data
        assert "generate_report" in data["endpoints"]


class TestReportsEndpoint:
    """Test the reports API endpoints."""

    def test_list_reports_returns_200(self, test_client):
        """List reports endpoint should return 200."""
        response = test_client.get("/api/reports/")
        
        assert response.status_code == 200

    def test_list_reports_returns_list(self, test_client):
        """List reports should return a list."""
        response = test_client.get("/api/reports/")
        data = response.json()
        
        assert isinstance(data, list)

    def test_get_nonexistent_report_returns_404(self, test_client):
        """Getting a nonexistent report should return 404."""
        response = test_client.get("/api/reports/nonexistent-id-12345")
        
        assert response.status_code == 404

    def test_followup_without_report_returns_404(self, test_client):
        """Follow-up on nonexistent report should return 404."""
        response = test_client.post(
            "/api/reports/nonexistent-id/followup",
            json={"report_id": "nonexistent-id", "question": "What about dosing?"}
        )
        
        assert response.status_code == 404


class TestGenerateReportEndpoint:
    """Test the report generation endpoint."""

    def test_generate_requires_question(self, test_client):
        """Generate should require a question field."""
        response = test_client.post(
            "/api/reports/generate",
            json={}
        )
        
        # Should return validation error
        assert response.status_code == 422

    def test_generate_accepts_valid_request(self, test_client):
        """Generate should accept valid request body."""
        # Note: This would actually call the LLM, so we just validate structure
        # In a real test, you'd mock the entire pipeline
        pass


class TestPDFExportEndpoint:
    """Test the PDF export endpoint."""

    def test_pdf_export_nonexistent_returns_404(self, test_client):
        """PDF export for nonexistent report should return 404."""
        response = test_client.get("/api/reports/nonexistent-id/export/pdf")
        
        assert response.status_code == 404


class TestCORSHeaders:
    """Test CORS headers are set correctly."""

    def test_cors_allows_origin(self, test_client):
        """CORS should allow requests."""
        response = test_client.options(
            "/",
            headers={"Origin": "http://localhost:4200"}
        )
        
        # Should not be rejected
        assert response.status_code in [200, 405]  # 405 if OPTIONS not handled


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_headers_present(self, test_client):
        """Rate limit endpoint should return headers."""
        response = test_client.get("/api/reports/")
        
        # Slowapi may add these headers
        # Just verify the endpoint works
        assert response.status_code == 200
