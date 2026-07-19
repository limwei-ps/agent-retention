def _seed_customer(db_session, make_customer, **kw):
    db_session.add(make_customer(**kw))
    db_session.commit()


def test_pitch_endpoint_streams_tokens_then_done(client, db_session, make_customer):
    _seed_customer(db_session, make_customer, id="CUST-00001", plan="fibre_300", archetype="heavy")
    resp = client.post("/api/customers/CUST-00001/pitch")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    body = resp.text
    assert "event: token" in body
    assert "event: done" in body
    assert '"grounding_ok": true' in body
    assert '"cache_hit": false' in body


def test_pitch_endpoint_cache_hit_on_second_call(client, db_session, make_customer):
    _seed_customer(db_session, make_customer, id="CUST-00001")
    client.post("/api/customers/CUST-00001/pitch")  # miss
    body = client.post("/api/customers/CUST-00001/pitch").text  # hit
    assert '"cache_hit": true' in body


def test_pitch_endpoint_force_regenerates(client, db_session, make_customer):
    _seed_customer(db_session, make_customer, id="CUST-00001")
    client.post("/api/customers/CUST-00001/pitch")
    body = client.post("/api/customers/CUST-00001/pitch", json={"force": True}).text
    assert '"cache_hit": false' in body  # force bypassed the cache


def test_pitch_endpoint_404_for_unknown_customer(client):
    assert client.post("/api/customers/CUST-99999/pitch").status_code == 404
