import time
from collections import defaultdict, deque
from typing import Deque, DefaultDict

from fastapi import HTTPException, Request


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: DefaultDict[str, Deque[float]] = defaultdict(deque)

    def enforce(self, key: str, limit: int, window_seconds: int) -> None:
        now = time.time()
        bucket = self._hits[key]

        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()

        if not bucket:
            self._hits.pop(key, None)
            bucket = self._hits[key]

        if len(bucket) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down and try again.",
            )

        bucket.append(now)


rate_limiter = InMemoryRateLimiter()


def build_rate_limit_key(request: Request, scope: str) -> str:
    client_host = request.client.host if request.client else "anonymous"
    return f"{scope}:{client_host}"
