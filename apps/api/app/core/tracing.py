"""Request trace id + logging correlation.

A ContextVar holds the current request's trace id. `TraceIdFilter` stamps it onto every log record
(as `ctx_trace_id` → `JsonFormatter` emits `trace_id`), so all lines for one request/generation share
an id. `TraceIdMiddleware` is a *pure ASGI* middleware (not Starlette's `BaseHTTPMiddleware`, which runs
the endpoint in a separate task where the ContextVar wouldn't propagate) that binds the id per request,
echoes/mints `X-Trace-Id`, and emits one structured request-complete log line.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("app.request")

TRACE_HEADER = b"x-trace-id"

_trace_id: ContextVar[str] = ContextVar("trace_id", default="")


def new_trace_id() -> str:
    return uuid.uuid4().hex[:12]


def get_trace_id() -> str:
    return _trace_id.get()


def bind_trace_id(trace_id: str) -> None:
    _trace_id.set(trace_id)


class TraceIdFilter(logging.Filter):
    """Stamp every record with the current trace id (empty string when unbound)."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.ctx_trace_id = get_trace_id()
        return True


class TraceIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        inbound = headers.get(TRACE_HEADER)
        trace_id = inbound.decode() if inbound else new_trace_id()
        bind_trace_id(trace_id)

        started = time.monotonic()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                message = {
                    **message,
                    "headers": [*(message.get("headers") or []), (TRACE_HEADER, trace_id.encode())],
                }
            await send(message)

        try:
            await self._app(scope, receive, send_wrapper)
        finally:
            logger.info(
                "request",
                extra={
                    "ctx_method": scope.get("method"),
                    "ctx_path": scope.get("path"),
                    "ctx_status": status_code,
                    "ctx_latency_ms": round((time.monotonic() - started) * 1000, 1),
                },
            )
