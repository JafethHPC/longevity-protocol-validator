"""
Redis Cache Service

Provides caching for reports with TTL expiration.
Falls back gracefully when Redis is unavailable.
"""
import json
from typing import Optional
import redis
from datetime import timedelta

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.report import ResearchReport

logger = get_logger(__name__)


class ReportCache:
    """Redis-based cache for research reports with TTL."""
    
    DEFAULT_TTL = timedelta(hours=24)
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connected = False
        self._connect()
    
    def _connect(self):
        """Attempt to connect to Redis."""
        try:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            self._client.ping()
            self._connected = True
            logger.info("Connected to Redis cache")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis not available, using in-memory fallback: {e}")
            self._connected = False
            self._fallback_cache = {}
    
    def _get_key(self, report_id: str) -> str:
        """Generate Redis key for a report."""
        return f"report:{report_id}"
    
    def set(self, report: ResearchReport, ttl: Optional[timedelta] = None) -> bool:
        """
        Store a report in cache.
        
        Args:
            report: The research report to cache
            ttl: Time-to-live for the cache entry (default: 24 hours)
        
        Returns:
            True if successful, False otherwise
        """
        ttl = ttl or self.DEFAULT_TTL
        key = self._get_key(report.id)
        
        try:
            if self._connected and self._client:
                self._client.setex(
                    key,
                    int(ttl.total_seconds()),
                    report.model_dump_json()
                )
                return True
            else:
                self._fallback_cache[key] = report.model_dump_json()
                return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def get(self, report_id: str) -> Optional[ResearchReport]:
        """
        Retrieve a report from cache.
        
        Args:
            report_id: The report ID to look up
        
        Returns:
            ResearchReport if found, None otherwise
        """
        key = self._get_key(report_id)
        
        try:
            if self._connected and self._client:
                data = self._client.get(key)
            else:
                data = self._fallback_cache.get(key)
            
            if data:
                return ResearchReport.model_validate_json(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def exists(self, report_id: str) -> bool:
        """Check if a report exists in cache."""
        key = self._get_key(report_id)
        
        try:
            if self._connected and self._client:
                return bool(self._client.exists(key))
            else:
                return key in self._fallback_cache
        except Exception:
            return False
    
    def delete(self, report_id: str) -> bool:
        """Delete a report from cache."""
        key = self._get_key(report_id)
        
        try:
            if self._connected and self._client:
                return bool(self._client.delete(key))
            else:
                if key in self._fallback_cache:
                    del self._fallback_cache[key]
                    return True
                return False
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def list_reports(self) -> list:
        """List all cached report IDs."""
        try:
            if self._connected and self._client:
                keys = self._client.keys("report:*")
                return [k.replace("report:", "") for k in keys]
            else:
                return [k.replace("report:", "") for k in self._fallback_cache.keys()]
        except Exception as e:
            logger.error(f"Cache list error: {e}")
            return []
    
    def get_all_reports_summary(self) -> list:
        """Get summary info for all cached reports."""
        summaries = []
        
        for report_id in self.list_reports():
            report = self.get(report_id)
            if report:
                summaries.append({
                    "id": report.id,
                    "question": report.question,
                    "generated_at": report.generated_at.isoformat(),
                    "papers_used": report.papers_used
                })
        
        return summaries
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._connected


report_cache = ReportCache()
