import json
import logging
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("sre_runbook_api.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        started = perf_counter()
        response: Response | None = None

        try:
            response = await call_next(request)
            return response
        except Exception:
            self._log(
                request,
                status_code=500,
                duration_ms=(perf_counter() - started) * 1000,
                level=logging.ERROR,
                event="request_failed",
            )
            raise
        finally:
            if response is not None:
                self._log(
                    request,
                    status_code=response.status_code,
                    duration_ms=(perf_counter() - started) * 1000,
                    level=logging.INFO,
                    event="request_completed",
                )

    @staticmethod
    def _log(
        request: Request,
        *,
        status_code: int,
        duration_ms: float,
        level: int,
        event: str,
    ) -> None:
        record = {
            "event": event,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "correlation_id": getattr(request.state, "correlation_id", None),
        }
        logger.log(level, json.dumps(record, separators=(",", ":")))
