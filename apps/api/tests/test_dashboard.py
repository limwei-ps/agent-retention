from datetime import timedelta

from app.core.config import settings
from app.core.timeutil import current_month_bounds


def test_summary_counts_expiring_this_month_by_tier(client, db_session, make_customer):
    start, end = current_month_bounds(settings.app_timezone)
    in_month = start + timedelta(days=(end - start).days // 2)
    before_month = start - timedelta(days=1)

    db_session.add_all(
        [
            make_customer(id="CUST-1", plan="fibre_100", contract_end_date=in_month),
            make_customer(id="CUST-2", plan="fibre_100", contract_end_date=in_month),
            make_customer(id="CUST-3", plan="fibre_500", contract_end_date=in_month),
            make_customer(id="CUST-4", plan="fibre_500", contract_end_date=before_month),  # excluded
        ]
    )
    db_session.commit()

    body = client.get("/api/dashboard/summary").json()
    assert body["expiring_this_month"] == 3  # CUST-4 excluded (previous month)

    by_id = {t["plan"]["id"]: t["count"] for t in body["by_tier"]}
    assert by_id["fibre_100"] == 2
    assert by_id["fibre_500"] == 1
    assert by_id["fibre_300"] == 0  # all tiers present, zero when none
    # total equals the sum of per-tier counts
    assert body["expiring_this_month"] == sum(t["count"] for t in body["by_tier"])


def test_summary_all_tiers_present(client):
    body = client.get("/api/dashboard/summary").json()
    assert [t["plan"]["id"] for t in body["by_tier"]] == [
        "fibre_100",
        "fibre_300",
        "fibre_500",
        "fibre_1000",
    ]
