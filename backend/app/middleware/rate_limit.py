"""In-memory rate limiter for AI endpoints.

Implements a sliding-window rate limiter with two backends:
  - ``InMemoryBackend``: default, suitable for single-instance / development.
  - ``RedisBackend``: used in production when ``REDIS_URL`` is set. Correct
    across multiple uvicorn workers because state lives in Redis, not in-process.

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


# ── Backend ABC ───────────────────────────────────────────────────────────────

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


# ── In-memory backend (development / single-worker) ───────────────────────────

class InMemoryBackend(RateLimitBackend):
    """
    Sliding-window rate limiter using in-memory storage.

    Thread-safe for async (single process). For multi-worker deployments,
    use RedisBackend instead.
    """

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.monotonic()
        self._cleanup_interval = 60.0  # seconds

    async def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, dict[str, Any]]:
        now = time.monotonic()

        if now - self._last_cleanup > self._cleanup_interval:
            await self.cleanup()
            self._last_cleanup = now

        window_start = now - window_seconds
        self._requests[key] = [ts for ts in self._requests[key] if ts > window_start]

        current_count = len(self._requests[key])
        remaining = max(0, max_requests - current_count - 1)

        if current_count >= max_requests:
            earliest = min(self._requests[key]) if self._requests[key] else now
            retry_after = int(earliest + window_seconds - now) + 1
            return False, {
                "remaining": 0,
                "limit": max_requests,
                "reset": retry_after,
                "window": window_seconds,
            }

        self._requests[key].append(now)
        return True, {
            "remaining": remaining,
            "limit": max_requests,
            "reset": window_seconds,
            "window": window_seconds,
        }

    async def cleanup(self) -> None:
        now = time.monotonic()
        empty_keys = [
            key for key, timestamps in self._requests.items()
            if not timestamps or max(timestamps) < now - 300
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
        import time

        now = time.time()
        window_start = now - window_seconds

        try:
            
            await self.redis.zremrangebyscore(key, 0, window_start)

            
            current_count = await self.redis.zcard(key)

            
            if current_count >= max_requests:
                oldest = await self.redis.zrange(key, 0, 0, withscores=True)

                if oldest:
                    oldest_time = oldest[0][1]
                    reset = int((oldest_time + window_seconds) - now)
                    reset = max(reset, 0)
                else:
                    reset = window_seconds

                return False, {
                    "remaining": 0,
                    "limit": max_requests,
                    "reset": reset,
                    "window": window_seconds,
                }

            # Add current request (sorted set: score = timestamp)
            await self.redis.zadd(key, {str(now): now})

            # Keep TTL as safety cleanup (not for logic)
            await self.redis.expire(key, window_seconds)

            return True, {
                "remaining": max_requests - current_count - 1,
                "limit": max_requests,
                "reset": window_seconds,
                "window": window_seconds,
            }

        except Exception:
            # Fail-open strategy (do not break API if Redis fails)
            return True, {
                "remaining": max_requests,
                "limit": max_requests,
                "reset": window_seconds,
                "window": window_seconds,
            }

    async def cleanup(self) -> None:
        """
        Redis handles cleanup automatically using key expiration.
        No manual cleanup required for sliding window rate limiting.
        """
        return
        
    
        

# ── Redis backend (production / multi-worker) ─────────────────────────────────

class RedisBackend(RateLimitBackend):
    """
    Sliding-window rate limiter backed by Redis.

    Uses a sorted set per key: members are unique request IDs, scores are
    timestamps. This gives exact sliding-window counts without a Lua script.

    Requires: redis[asyncio] — listed in pyproject.toml dependencies.
    """

    def __init__(self, redis_url: str) -> None:
        try:
            import redis.asyncio as aioredis
        except ImportError as exc:
            raise RuntimeError(
                "redis[asyncio] is not installed but REDIS_URL is set. "
                "Add 'redis[asyncio]' to backend/pyproject.toml dependencies "
                "and reinstall: pip install -e ."
            ) from exc
        self._client = aioredis.from_url(redis_url, decode_responses=True)

    async def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, dict[str, Any]]:
        import uuid
        now = time.time()
        window_start = now - window_seconds

        pipe = self._client.pipeline()
        # Remove timestamps outside the current window
        pipe.zremrangebyscore(key, "-inf", window_start)
        # Count remaining in window
        pipe.zcard(key)
        # Add current request (scored by timestamp, unique member)
        member = f"{now}:{uuid.uuid4().hex}"
        pipe.zadd(key, {member: now})
        # Expire the key after the window so Redis cleans up automatically
        pipe.expire(key, window_seconds + 1)
        results = await pipe.execute()

        current_count = results[1]  # count BEFORE this request was added

        if current_count >= max_requests:
            # Roll back the zadd — request is rejected
            await self._client.zrem(key, member)
            # Find when the oldest request in the window expires
            oldest = await self._client.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window_seconds - now) + 1
            else:
                retry_after = window_seconds
            return False, {
                "remaining": 0,
                "limit": max_requests,
                "reset": retry_after,
                "window": window_seconds,
            }

        remaining = max(0, max_requests - current_count - 1)
        return True, {
            "remaining": remaining,
            "limit": max_requests,
            "reset": window_seconds,
            "window": window_seconds,
        }

    async def cleanup(self) -> None:
        # Redis TTLs handle cleanup automatically via the expire() call above
        pass


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mask_redis_url(url: str) -> str:
    """
    Mask the password in a Redis URL for safe logging.

        redis://:password@host:port/db      →  redis://:***@host:port/db
        redis://user:password@host:port/db  →  redis://user:***@host:port/db
        redis://host:port/db                →  redis://host:port/db  (unchanged)
    """
    if "@" not in url:
        return url
    scheme_and_creds, hostpart = url.rsplit("@", 1)
    creds = scheme_and_creds.split("//", 1)[-1]
    if ":" in creds:
        # Mask everything after the last colon in the credentials segment
        prefix = scheme_and_creds.rsplit(":", 1)[0]
        return f"{prefix}:***@{hostpart}"
    return url


# ── Backend factory ───────────────────────────────────────────────────────────

def _make_backend() -> RateLimitBackend:
    """
    Return a RedisBackend if REDIS_URL is configured, else InMemoryBackend.
    Called once at import time — settings are already loaded by then.
    """
    settings = get_settings()
    if settings.redis_url:
        logger.info("Rate limiter using Redis backend: %s", _mask_redis_url(settings.redis_url))
        return RedisBackend(settings.redis_url)
    logger.info("Rate limiter using in-memory backend (single-instance only)")
    return InMemoryBackend()


_backend = _make_backend()

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