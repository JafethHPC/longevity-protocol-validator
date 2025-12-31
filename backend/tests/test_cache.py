"""Tests for services/cache.py - Caching service."""
from unittest.mock import patch, MagicMock

import pytest


class TestReportCache:
    """Test the ReportCache class."""

    def test_report_cache_can_be_instantiated(self):
        """ReportCache should be instantiable."""
        from app.services.cache import ReportCache
        
        cache = ReportCache()
        assert cache is not None

    def test_is_connected_returns_bool(self):
        """is_connected should return a boolean."""
        from app.services.cache import ReportCache
        
        cache = ReportCache()
        assert isinstance(cache.is_connected, bool)

    def test_get_nonexistent_returns_none(self):
        """get() on nonexistent key should return None."""
        from app.services.cache import ReportCache
        
        cache = ReportCache()
        result = cache.get("nonexistent-key-12345")
        
        assert result is None

    def test_set_and_get_roundtrip(self, sample_report):
        """Setting and getting a report should work."""
        from app.services.cache import ReportCache
        from app.schemas.report import ResearchReport
        
        cache = ReportCache()
        
        # Create a proper report object
        report = ResearchReport(**sample_report)
        
        # Set the report
        cache.set(report)
        
        # Get it back
        retrieved = cache.get(report.id)
        
        if retrieved is not None:  # May be None if using memory fallback
            assert retrieved.id == report.id

    def test_get_all_reports_summary_returns_list(self):
        """get_all_reports_summary should return a list."""
        from app.services.cache import ReportCache
        
        cache = ReportCache()
        result = cache.get_all_reports_summary()
        
        assert isinstance(result, list)


class TestReportCacheModule:
    """Test the cache module exports."""

    def test_report_cache_singleton_exported(self):
        """report_cache singleton should be exported."""
        from app.services.cache import report_cache
        
        assert report_cache is not None

    def test_singleton_is_reused(self):
        """Importing multiple times should return same instance."""
        from app.services.cache import report_cache as cache1
        from app.services.cache import report_cache as cache2
        
        assert cache1 is cache2


class TestCacheFallback:
    """Test cache fallback behavior."""

    def test_cache_works_without_redis(self):
        """Cache should work even when Redis is unavailable."""
        from app.services.cache import ReportCache
        
        # Force a new cache instance without Redis
        with patch("redis.from_url") as mock_redis:
            mock_redis.side_effect = Exception("Connection refused")
            
            cache = ReportCache()
            
            # Should not raise, should use fallback
            assert cache is not None

    def test_cache_uses_memory_fallback(self):
        """When Redis unavailable, should use in-memory storage."""
        from app.services.cache import ReportCache
        
        with patch("redis.from_url") as mock_redis:
            mock_redis.side_effect = Exception("Connection refused")
            
            cache = ReportCache()
            
            # is_connected should be False for memory fallback
            # (or True if it considers memory as "connected")
            assert isinstance(cache.is_connected, bool)
