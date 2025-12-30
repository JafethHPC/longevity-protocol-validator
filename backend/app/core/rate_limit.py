"""
Rate Limiting Middleware

Protects API endpoints from abuse using slowapi.
Uses Redis for distributed rate limiting when available.
"""
import redis
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_identifier(request: Request) -> str:
    """
    Get a unique identifier for rate limiting.
    Uses IP address by default, can be extended for API keys.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    return get_remote_address(request)


def _get_storage_uri() -> str:
    """
    Get storage URI for rate limiting.
    Tests Redis connection first, falls back to memory if unavailable.
    """
    redis_uri = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
    
    try:
        # Test Redis connection
        client = redis.from_url(redis_uri, socket_connect_timeout=2)
        client.ping()
        logger.info("Rate limiter using Redis storage")
        return redis_uri
    except (redis.ConnectionError, redis.TimeoutError):
        logger.warning("Redis not available for rate limiting, using in-memory storage")
        return "memory://"


limiter = Limiter(
    key_func=_get_identifier,
    storage_uri=_get_storage_uri(),
    default_limits=["100/minute"],
    strategy="fixed-window"
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. {exc.detail}",
            "retry_after": getattr(exc, 'retry_after', 60)
        },
        headers={
            "Retry-After": str(getattr(exc, 'retry_after', 60)),
            "X-RateLimit-Limit": request.state.view_rate_limit if hasattr(request.state, 'view_rate_limit') else "unknown"
        }
    )


REPORT_GENERATE_LIMIT = "3/minute"
REPORT_GET_LIMIT = "30/minute"
FOLLOWUP_LIMIT = "10/minute"
PDF_EXPORT_LIMIT = "5/minute"
