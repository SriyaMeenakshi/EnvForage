"""In-memory rate limiter for AI endpoints.

Implements a sliding-window rate limiter using an in-memory store.
This is suitable for single-instance deployments. For multi-instance
production, swap the backend to Redis (see ``RateLimitBackend`` ABC).

Design:
    - Rate limits are per-client-IP
    - AI endpoints get stricter limits than general API endpoints
    - Returns standard HTTP 429 with Retry-After header
    - Configurable via Settings (rate_limit_ai_rpm, rate_limit_general_rpm)

Usage::

    from app.middleware.rate_limit import RateLimiter, ai_rate_limit

    # As a FastAPI dependency
    @router.post("/troubleshoot")
    async def troubleshoot(
        request: TroubleshootRequest,
        _rate_limit: None = Depends(ai_rate_limit),
    ):
        ...
"""
import time
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any

from fastapi import Depends, HTTPException, Request

from app.config import get_settings

logger = logging.getLogger(__name__)


# ── Backend ABC (swap for Redis in production) ────────────────────────────────

class RateLimitBackend(ABC):
    """Abstract rate limit storage backend."""

    @abstractmethod
    async def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, dict[str, Any]]:
        """
        Check if a request is allowed under the rate limit.

        Args:
            key: Unique identifier (e.g. IP address).
            max_requests: Maximum requests allowed in the window.
            window_seconds: Time window in seconds.

        Returns:
            Tuple of (allowed: bool, info: dict with remaining, reset, limit).
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Remove expired entries. Called periodically."""
        ...


class InMemoryBackend(RateLimitBackend):
    """
    Sliding-window rate limiter using in-memory storage.

    Thread-safe for async (single process). For multi-worker deployments,
    use the Redis backend instead.
    """

    def __init__(self) -> None:
        # key -> list of timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.monotonic()
        self._cleanup_interval = 60.0  # seconds

    async def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, dict[str, Any]]:
        now = time.monotonic()

        # Periodic cleanup
        if now - self._last_cleanup > self._cleanup_interval:
            await self.cleanup()
            self._last_cleanup = now

        # Remove expired timestamps
        window_start = now - window_seconds
        self._requests[key] = [ts for ts in self._requests[key] if ts > window_start]

        current_count = len(self._requests[key])
        remaining = max(0, max_requests - current_count - 1)

        if current_count >= max_requests:
            # Calculate when the earliest request will expire
            earliest = min(self._requests[key]) if self._requests[key] else now
            retry_after = int(earliest + window_seconds - now) + 1
            return False, {
                "remaining": 0,
                "limit": max_requests,
                "reset": retry_after,
                "window": window_seconds,
            }

        # Allow and record
        self._requests[key].append(now)
        return True, {
            "remaining": remaining,
            "limit": max_requests,
            "reset": window_seconds,
            "window": window_seconds,
        }

    async def cleanup(self) -> None:
        """Remove keys with no recent requests."""
        now = time.monotonic()
        empty_keys = [
            key for key, timestamps in self._requests.items()
            if not timestamps or max(timestamps) < now - 300  # 5 min stale
        ]
        for key in empty_keys:
            del self._requests[key]
        if empty_keys:
            logger.debug("Rate limiter cleanup: removed %d stale keys", len(empty_keys))

class RedisBackend(RateLimitBackend):
    def __init__(self, redis_url: str):
        import redis.asyncio as redis
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def is_allowed(self, key: str, max_requests: int, window_seconds: int):
        now = time.time()
        window_start = now - window_seconds

        await self.redis.zremrangebyscore(key, 0, window_start)

        current_count = await self.redis.zcard(key)

        if current_count >= max_requests:
            ttl = await self.redis.ttl(key)
            return False, {
                "remaining": 0,
                "limit": max_requests,
                "reset": ttl if ttl > 0 else window_seconds,
                "window": window_seconds,
            }

        await self.redis.zadd(key, {str(now): now})
        await self.redis.expire(key, window_seconds)

        return True, {
            "remaining": max_requests - current_count - 1,
            "limit": max_requests,
            "reset": window_seconds,
            "window": window_seconds,
        }

    async def cleanup(self) -> None:
        """
        Redis handles cleanup automatically using key expiration.
        No manual clean up required for sliding window rate limiting.
        """
        return
        
    
        

# ── Singleton backend ─────────────────────────────────────────────────────────


settings = get_settings()

if settings.redis_url:
    _backend = RedisBackend(settings.redis_url)
else:
    _backend = InMemoryBackend()


# ── Rate Limiter ──────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Configurable rate limiter for FastAPI dependency injection.

    Usage::

        limiter = RateLimiter(max_requests=10, window_seconds=60)

        @router.post("/endpoint")
        async def endpoint(_: None = Depends(limiter)):
            ...
    """

    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: int = 60,
        backend: RateLimitBackend | None = None,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.backend = backend or _backend

    async def __call__(self, request: Request) -> None:
        """FastAPI dependency — raises HTTPException(429) if rate limited."""
        # Extract client IP
        client_ip = self._get_client_ip(request)
        key = f"rate_limit:{request.url.path}:{client_ip}"

        allowed, info = await self.backend.is_allowed(
            key, self.max_requests, self.window_seconds,
        )

        if not allowed:
            logger.warning(
                "Rate limit exceeded: %s on %s (limit: %d/%ds)",
                client_ip, request.url.path, self.max_requests, self.window_seconds,
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": (
                        f"Too many requests. Limit: {self.max_requests} per "
                        f"{self.window_seconds}s. Try again in {info['reset']}s."
                    ),
                    "retry_after": info["reset"],
                },
                headers={"Retry-After": str(info["reset"])},
            )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For behind proxies."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# ── Pre-configured limiters ───────────────────────────────────────────────────

# AI endpoints: 10 requests per minute (LLM calls are expensive)
ai_rate_limit = RateLimiter(max_requests=10, window_seconds=60)

# Repair endpoints: 20 requests per minute (template rendering is cheap)
repair_rate_limit = RateLimiter(max_requests=20, window_seconds=60)

# General API: 60 requests per minute
general_rate_limit = RateLimiter(max_requests=60, window_seconds=60)
