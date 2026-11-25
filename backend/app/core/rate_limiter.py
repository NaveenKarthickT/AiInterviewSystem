import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict

# Simple in‑memory token bucket per IP
import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict

# Simple in‑memory token bucket per IP
class RateLimiter(BaseHTTPMiddleware):
    """Token‑bucket rate limiter.
    - General endpoints: `limit_per_minute` (default 60).
    - Auth endpoints (`/api/v1/auth/*`): `auth_limit` (default 10).
    """
    def __init__(self, app, limit_per_minute: int = 60, auth_limit: int = 10):
        super().__init__(app)
        self.limit = limit_per_minute
        self.auth_limit = auth_limit
        self.tokens = defaultdict(lambda: [self.limit, time.time()])  # [remaining, last_refill]
        self.auth_tokens = defaultdict(lambda: [self.auth_limit, time.time()])

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now = time.time()
        # Choose bucket based on whether this is an auth request
        bucket = self.auth_tokens if path.startswith('/api/v1/auth') else self.tokens
        remaining, last = bucket[client_ip]
        # Refill tokens based on elapsed time
        elapsed = now - last
        refill_rate = (self.limit if bucket is self.tokens else self.auth_limit) / 60.0
        new_tokens = min(remaining + elapsed * refill_rate, self.limit if bucket is self.tokens else self.auth_limit)
        bucket[client_ip] = [new_tokens, now]
        if new_tokens < 1:
            raise HTTPException(status_code=429, detail="Too Many Requests")
        # Consume a token for this request
        bucket[client_ip][0] = new_tokens - 1
        response = await call_next(request)
        return response

# Preserve the original name used in `app.main`
RateLimiterMiddleware = RateLimiter


