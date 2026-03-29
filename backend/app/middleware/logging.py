import time
import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Bind request context
        log = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )
        log.info("request_started")

        try:
            response = await call_next(request)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms}ms"
            return response
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log.error("request_failed", error=str(exc), duration_ms=duration_ms)
            raise
