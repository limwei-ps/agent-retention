"""Metrics controller — Prometheus text exposition of the in-process registry."""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.core.metrics import METRICS

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def metrics() -> Response:
    return Response(
        content=METRICS.render_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
