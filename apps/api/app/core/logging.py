"""Structured (JSON) logging setup.

Kept minimal for the scaffold; the AI layer will emit per-call cost/latency logs
through this same logger (spec §4.8).
"""

from __future__ import annotations

import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Attach structured extras passed via logger.info(..., extra={...}).
        for key, value in getattr(record, "__dict__", {}).items():
            if key.startswith("ctx_"):
                payload[key[4:]] = value
        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    from app.core.tracing import TraceIdFilter

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(TraceIdFilter())  # stamp trace_id onto every line
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
