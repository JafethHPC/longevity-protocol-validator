"""
Rate Limiting Middleware

Protects API endpoints from abuse using slowapi.
Uses Redis for distributed rate limiting when available.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings


def _get_identifier(request: Request) -> str:
    """
    Get a unique identifier for rate limiting.
    Uses IP address by default, can be extended for API keys.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    return get_remote_address(request)


def _create_redis_uri() -> str:
    """Create Redis URI for rate limiting storage."""
    return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"


limiter = Limiter(
    key_func=_get_identifier,
    storage_uri=_create_redis_uri(),
    storage_options={"socket_connect_timeout": 2},
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
