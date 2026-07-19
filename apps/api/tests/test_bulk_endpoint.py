"""Bulk endpoint tests. `TestClient` runs BackgroundTasks to completion before returning, so a POST
can be immediately polled for the finished batch."""

from app.services.batch_registry import BatchRegistry


def _seed(factory, make_customer, ids):
    with factory() as db:
        for cid in ids:
            db.add(make_customer(id=cid, name=f"Cust {cid}"))
        db.commit()


def test_bulk_post_then_poll_all_succeed(bulk_client, make_customer):
    client, factory = bulk_client
    ids = ["CUST-1", "CUST-2", "CUST-3"]
    _seed(factory, make_customer, ids)

    resp = client.post("/api/pitches/bulk", json={"customer_ids": ids})
    assert resp.status_code == 200
    created = resp.json()
    assert created["total"] == 3
    batch_id = created["batch_id"]

    status = client.get(f"/api/pitches/bulk/{batch_id}").json()
    assert status["complete"] is True
    assert status["live"] is True
    assert status["succeeded"] == 3
    assert status["failed"] == 0
    assert status["completed"] == 3
    assert len(status["items"]) == 3
    assert all(item["pitch_id"] is not None for item in status["items"])


def test_bulk_partial_failure_isolation(bulk_client, make_customer):
    client, factory = bulk_client
    _seed(factory, make_customer, ["CUST-1", "CUST-2"])
    ids = ["CUST-1", "CUST-MISSING", "CUST-2"]

    batch_id = client.post("/api/pitches/bulk", json={"customer_ids": ids}).json()["batch_id"]
    status = client.get(f"/api/pitches/bulk/{batch_id}").json()

    assert status["succeeded"] == 2
    assert status["failed"] == 1
    missing = next(i for i in status["items"] if i["customer_id"] == "CUST-MISSING")
    assert missing["status"] == "failed"
    assert missing["error"] == "customer not found"


def test_bulk_dedups_customer_ids(bulk_client, make_customer):
    client, factory = bulk_client
    _seed(factory, make_customer, ["CUST-1"])

    resp = client.post("/api/pitches/bulk", json={"customer_ids": ["CUST-1", "CUST-1", "CUST-1"]})
    assert resp.json()["total"] == 1


def test_bulk_stream_emits_progress_then_done(bulk_client, make_customer):
    client, factory = bulk_client
    ids = ["CUST-1", "CUST-2"]
    _seed(factory, make_customer, ids)
    batch_id = client.post("/api/pitches/bulk", json={"customer_ids": ids}).json()["batch_id"]

    body = client.get(f"/api/pitches/bulk/{batch_id}/stream").text
    assert "event: progress" in body
    assert "event: done" in body
    assert '"succeeded": 2' in body


def test_bulk_poll_db_fallback_after_registry_evicted(bulk_client, make_customer):
    client, factory = bulk_client
    ids = ["CUST-1", "CUST-2"]
    _seed(factory, make_customer, ids)
    batch_id = client.post("/api/pitches/bulk", json={"customer_ids": ids}).json()["batch_id"]

    # Simulate a process restart / eviction: the registry no longer holds the batch.
    client.app.state.batch_registry = BatchRegistry()

    status = client.get(f"/api/pitches/bulk/{batch_id}").json()
    assert status["live"] is False
    assert status["succeeded"] == 2  # reconstructed from the persisted ready pitches
    assert status["complete"] is True


def test_bulk_unknown_batch_404(bulk_client):
    client, _ = bulk_client
    assert client.get("/api/pitches/bulk/999").status_code == 404


def test_bulk_empty_customer_ids_422(bulk_client):
    client, _ = bulk_client
    assert client.post("/api/pitches/bulk", json={"customer_ids": []}).status_code == 422
