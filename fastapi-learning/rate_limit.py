import os
import threading
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_WINDOW_SECONDS = 60


rate_limit_middleware_instance = None


def reset_rate_limit_storage():
    global rate_limit_middleware_instance
    if rate_limit_middleware_instance is not None:
        with rate_limit_middleware_instance.lock:
            rate_limit_middleware_instance.clients.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = RATE_LIMIT_PER_MINUTE, window: int = RATE_LIMIT_WINDOW_SECONDS):
        super().__init__(app)
        self.default_limit = limit
        self.default_window = window
        self.clients = {}
        self.lock = threading.Lock()
        global rate_limit_middleware_instance
        rate_limit_middleware_instance = self

    async def dispatch(self, request: Request, call_next):
        limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", str(self.default_limit)))
        window = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", str(self.default_window)))
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        with self.lock:
            entry = self.clients.get(client_ip)
            if entry is None or entry.get("limit") != limit:
                entry = {"tokens": limit - 1, "last": now, "limit": limit}
                self.clients[client_ip] = entry
                remaining = limit - 1
            else:
                elapsed = now - entry["last"]
                refill = (elapsed / window) * limit
                entry["tokens"] = min(limit, entry["tokens"] + refill)
                entry["last"] = now

                if entry["tokens"] >= 1:
                    entry["tokens"] -= 1
                    remaining = int(entry["tokens"])
                    self.clients[client_ip] = entry
                else:
                    retry_after = int(window - (elapsed % window))
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded. Try again later."},
                        headers={"Retry-After": str(retry_after)},
                    )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
