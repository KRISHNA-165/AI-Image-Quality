"""
Request Logging & Observability Middleware.
Emits structured JSON access logs with trace IDs, method, status, client IP, and latency.
"""

import time
import uuid
import json
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.metrics import metrics_collector

logger = logging.getLogger("api.access")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or propagate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id

        start_time = time.perf_counter()
        metrics_collector.record_request_start()

        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            metrics_collector.record_request_end(method, path, 500, duration_ms)
            
            log_entry = {
                "level": "ERROR",
                "request_id": request_id,
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "status": 500,
                "latency_ms": duration_ms,
                "error": str(exc),
            }
            logger.error(json.dumps(log_entry))
            raise exc

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        metrics_collector.record_request_end(method, path, status_code, duration_ms)

        # Attach request ID header to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-MS"] = str(duration_ms)

        # Emit structured log entry (skip noisy static asset polls if status 200/304)
        if not path.startswith("/storage/") or status_code >= 400:
            log_entry = {
                "request_id": request_id,
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "status": status_code,
                "latency_ms": duration_ms,
            }
            if status_code >= 400:
                logger.warning(json.dumps(log_entry))
            else:
                logger.info(json.dumps(log_entry))

        return response
