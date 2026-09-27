"""
Lightweight in-memory sliding-window rate limiter middleware.
For multi-instance production deployments, back this with Redis instead.
"""
import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config.settings import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int | None = None):
        super().__init__(app)
        self.limit = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.window_seconds = 60
        self._hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_key = self._client_key(request)
        now = time.monotonic()
        hits = self._hits[client_key]

        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down and try again shortly."},
            )

        hits.append(now)
        return await call_next(request)

    @staticmethod
    def _client_key(request: Request) -> str:
        auth_header = request.headers.get("authorization")
        if auth_header:
            return auth_header
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
