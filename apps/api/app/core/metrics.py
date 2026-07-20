"""In-process metrics registry with Prometheus text exposition — no external dependency.

A single-instance set of counters for the AI/observability layer, rendered at GET /api/metrics.
Thread-safe (sync SQLAlchemy calls may run in a threadpool); increments are cheap. Not durable across
restarts — a production build would use a real metrics backend (see README out-of-scope).
"""

from __future__ import annotations

import threading

Labels = dict[str, str]
_Key = tuple[str, tuple[tuple[str, str], ...]]


def _fmt(value: float) -> str:
    return str(int(value)) if value == int(value) else repr(value)


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[_Key, float] = {}
        self._help: dict[str, str] = {}

    def register(self, name: str, help_text: str) -> None:
        """Declare a counter so its HELP/TYPE appear even before the first increment."""
        self._help[name] = help_text

    def inc(self, name: str, labels: Labels | None = None, amount: float = 1.0) -> None:
        key: _Key = (name, tuple(sorted((labels or {}).items())))
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + amount

    def render_prometheus(self) -> str:
        with self._lock:
            counters = dict(self._counters)
        names = sorted(set(self._help) | {name for name, _ in counters})

        lines: list[str] = []
        for name in names:
            if name in self._help:
                lines.append(f"# HELP {name} {self._help[name]}")
            lines.append(f"# TYPE {name} counter")
            series = sorted((labels, v) for (n, labels), v in counters.items() if n == name)
            if not series:
                lines.append(f"{name} 0")
            for labels, value in series:
                label_str = "{" + ",".join(f'{k}="{v}"' for k, v in labels) + "}" if labels else ""
                lines.append(f"{name}{label_str} {_fmt(value)}")
        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()


METRICS = Metrics()
METRICS.register("pitch_generations_total", "Pitches generated, by terminal outcome.")
METRICS.register("pitch_cache_hits_total", "Pitch requests served from cache.")
METRICS.register("pitch_regenerations_total", "Regeneration attempts after ungrounded output.")
METRICS.register("pitch_fallbacks_total", "Fallback advances, by hop.")
METRICS.register("pitch_tokens_total", "Total LLM tokens billed (prompt + completion).")
METRICS.register("pitch_cost_usd_total", "Total estimated LLM cost in USD.")
METRICS.register("http_requests_total", "HTTP requests, by method and status.")
