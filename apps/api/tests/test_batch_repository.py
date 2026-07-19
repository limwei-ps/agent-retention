from app.repositories.batch_repository import SqlBatchRepository


def test_create_and_get_round_trip(db_session):
    repo = SqlBatchRepository(db_session)

    batch = repo.create(["CUST-1", "CUST-2", "CUST-3"], total=3)

    assert batch.id is not None
    assert batch.total == 3
    assert batch.created_at is not None

    fetched = repo.get(batch.id)
    assert fetched is not None
    assert fetched.customer_ids == ["CUST-1", "CUST-2", "CUST-3"]


def test_get_unknown_returns_none(db_session):
    assert SqlBatchRepository(db_session).get(999) is None
