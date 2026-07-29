"""HTTP middleware — correlation id + request logging."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("evonas.presentation.api")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Attach X-Request-ID and log request duration."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            status = response.status_code if response is not None else 500
            if response is not None:
                response.headers["X-Request-ID"] = request_id
            logger.info(
                "%s %s -> %s (%.1fms) rid=%s",
                request.method,
                request.url.path,
                status,
                duration_ms,
                request_id,
            )
