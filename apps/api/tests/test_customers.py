from sqlalchemy import event

from app.models.pitch import Pitch, PitchStatus


def _seed(db, make_customer, rows):
    for kwargs in rows:
        db.add(make_customer(**kwargs))
    db.commit()


def test_list_returns_paginated_envelope(client, db_session, make_customer):
    _seed(
        db_session,
        make_customer,
        [
            {"id": "CUST-00001", "name": "Alice Tan"},
            {"id": "CUST-00002", "name": "Bob Lee"},
            {"id": "CUST-00003", "name": "Cathy Wong"},
        ],
    )
    resp = client.get("/api/customers", params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["data"]) == 2
    assert set(body["data"][0]) >= {"id", "name", "current_plan", "tenure_months", "avg_monthly_gb"}


def test_search_matches_name_or_id(client, db_session, make_customer):
    _seed(
        db_session,
        make_customer,
        [
            {"id": "CUST-00001", "name": "Alice Tan"},
            {"id": "CUST-00002", "name": "Bob Lee"},
        ],
    )
    by_name = client.get("/api/customers", params={"search": "alice"}).json()
    assert [c["id"] for c in by_name["data"]] == ["CUST-00001"]

    by_id = client.get("/api/customers", params={"search": "00002"}).json()
    assert [c["id"] for c in by_id["data"]] == ["CUST-00002"]


def test_filter_by_plan(client, db_session, make_customer):
    _seed(
        db_session,
        make_customer,
        [
            {"id": "CUST-00001", "plan": "fibre_100"},
            {"id": "CUST-00002", "plan": "fibre_500"},
        ],
    )
    resp = client.get("/api/customers", params={"plan": "fibre_500"}).json()
    assert [c["id"] for c in resp["data"]] == ["CUST-00002"]
    assert resp["data"][0]["current_plan"]["name"] == "TIME Fibre 500"


def test_sort_by_tenure_desc(client, db_session, make_customer):
    _seed(
        db_session,
        make_customer,
        [
            {"id": "CUST-00001", "tenure_months": 5},
            {"id": "CUST-00002", "tenure_months": 40},
            {"id": "CUST-00003", "tenure_months": 20},
        ],
    )
    resp = client.get("/api/customers", params={"sort": "tenure", "order": "desc"}).json()
    assert [c["id"] for c in resp["data"]] == ["CUST-00002", "CUST-00003", "CUST-00001"]


def test_detail_returns_offer_ladder_and_usage(client, db_session, make_customer):
    _seed(
        db_session,
        make_customer,
        [{"id": "CUST-00042", "plan": "fibre_300", "archetype": "heavy", "tenure_months": 12}],
    )
    body = client.get("/api/customers/CUST-00042").json()
    assert body["id"] == "CUST-00042"
    assert body["offer_ladder"]["recommended"] == "upsell"
    assert len(body["offer_ladder"]["rungs"]) == 3
    assert body["usage_history"][0]["month"] == "2026-06"
    assert body["latest_pitch"] is None


def test_detail_404_for_unknown(client):
    assert client.get("/api/customers/CUST-99999").status_code == 404


def test_list_avoids_n_plus_one(client, db_session, make_customer):
    # 5 customers each with a pitch — a naive lazy load would fire 5 extra queries.
    for i in range(5):
        db_session.add(make_customer(id=f"CUST-{i:05d}"))
        db_session.flush()
        db_session.add(Pitch(customer_id=f"CUST-{i:05d}", status=PitchStatus.ready, text="x"))
    db_session.commit()

    engine = db_session.get_bind()
    count = {"queries": 0}

    def _on_exec(*_args, **_kwargs):
        count["queries"] += 1

    event.listen(engine, "after_cursor_execute", _on_exec)
    try:
        resp = client.get("/api/customers", params={"page_size": 5})
    finally:
        event.remove(engine, "after_cursor_execute", _on_exec)

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 5
    assert all(c["latest_pitch_status"] == "ready" for c in data)
    # count + page + one batched selectin for all pitches ≈ 3 — bounded, not O(rows).
    assert count["queries"] <= 3


def test_pagination_stable_with_tied_sort_values(client, db_session, make_customer):
    # All identical tenure → the sort column ties; the id tiebreaker must keep paging total.
    for i in range(6):
        db_session.add(make_customer(id=f"CUST-{i:05d}", tenure_months=12))
    db_session.commit()

    seen: list[str] = []
    for page in (1, 2, 3):
        body = client.get(
            "/api/customers",
            params={"sort": "tenure", "order": "asc", "page": page, "page_size": 2},
        ).json()
        seen += [c["id"] for c in body["data"]]

    assert len(seen) == 6
    assert len(set(seen)) == 6  # no duplicates and no omissions across pages
