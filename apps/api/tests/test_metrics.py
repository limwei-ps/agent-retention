"""Metrics endpoint (Prometheus text) + counter increments from the AI layer."""

from __future__ import annotations

import re

import pytest

from app.core.metrics import METRICS


@pytest.fixture(autouse=True)
def _reset_metrics():
    METRICS.reset()
    yield
    METRICS.reset()


def _seed(db_session, make_customer, **kw):
    db_session.add(make_customer(**kw))
    db_session.commit()


def test_metrics_endpoint_exposes_prometheus(client):
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    body = resp.text
    assert "# TYPE pitch_generations_total counter" in body
    assert "http_requests_total" in body  # registered even before any data


def test_generation_increments_counters(client, db_session, make_customer):
    _seed(db_session, make_customer, id="CUST-00001")
    client.post("/api/customers/CUST-00001/pitch")  # mock generation

    body = client.get("/api/metrics").text
    assert 'pitch_generations_total{outcome="generated"} 1' in body
    tokens = re.search(r"^pitch_tokens_total (\d+)$", body, re.M)
    assert tokens and int(tokens.group(1)) > 0


def test_cache_hit_increments_counter(client, db_session, make_customer):
    _seed(db_session, make_customer, id="CUST-00001")
    client.post("/api/customers/CUST-00001/pitch")  # miss
    client.post("/api/customers/CUST-00001/pitch")  # hit
    assert "pitch_cache_hits_total 1" in client.get("/api/metrics").text


def test_done_event_carries_trace_id(client, db_session, make_customer):
    _seed(db_session, make_customer, id="CUST-00001")
    body = client.post("/api/customers/CUST-00001/pitch").text
    assert '"trace_id"' in body
