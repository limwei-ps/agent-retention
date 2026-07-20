"""Request trace id: minted per request, echoed when provided, returned as X-Trace-Id."""

from __future__ import annotations


def test_response_carries_a_trace_id(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    trace = resp.headers.get("x-trace-id")
    assert trace and len(trace) >= 8


def test_inbound_trace_id_is_echoed(client):
    resp = client.get("/api/health", headers={"x-trace-id": "abc123def456"})
    assert resp.headers.get("x-trace-id") == "abc123def456"


def test_each_request_gets_a_distinct_trace_id(client):
    a = client.get("/api/health").headers["x-trace-id"]
    b = client.get("/api/health").headers["x-trace-id"]
    assert a != b
