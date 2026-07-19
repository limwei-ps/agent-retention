from datetime import date


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
