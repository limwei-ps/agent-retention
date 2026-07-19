import asyncio

from app.services.batch_registry import BatchRegistry


def test_snapshot_of_unknown_batch_is_none():
    assert BatchRegistry().snapshot(1) is None


async def test_state_transitions_and_counts():
    reg = BatchRegistry()
    reg.create(1, ["A", "B", "C"])

    snap = reg.snapshot(1)
    assert snap is not None
    assert snap.total == 3
    assert snap.pending == 3
    assert snap.live is True
    assert snap.complete is False

    await reg.mark_running(1, "A")
    await reg.mark_succeeded(1, "A", pitch_id=42)
    await reg.mark_failed(1, "B", error="boom")

    snap = reg.snapshot(1)
    assert snap.succeeded == 1
    assert snap.failed == 1
    assert snap.pending == 1
    assert snap.completed == 2
    a = next(i for i in snap.items if i.customer_id == "A")
    assert a.pitch_id == 42
    b = next(i for i in snap.items if i.customer_id == "B")
    assert b.error == "boom"

    await reg.mark_complete(1)
    assert reg.snapshot(1).complete is True


async def test_wait_for_change_wakes_on_update():
    reg = BatchRegistry()
    reg.create(1, ["A"])
    start_version = reg.snapshot(1).version

    async def advance():
        await asyncio.sleep(0.01)
        await reg.mark_succeeded(1, "A", pitch_id=1)

    task = asyncio.create_task(advance())
    new_version = await reg.wait_for_change(1, start_version)
    await task

    assert new_version > start_version


async def test_wait_for_change_returns_immediately_if_already_advanced():
    reg = BatchRegistry()
    reg.create(1, ["A"])
    await reg.mark_succeeded(1, "A", pitch_id=1)  # version now ahead of 0

    # Passing an already-stale version must not block (no missed terminal state).
    new_version = await asyncio.wait_for(reg.wait_for_change(1, 0), timeout=1)
    assert new_version > 0


async def test_evicts_oldest_completed_when_over_cap():
    reg = BatchRegistry(max_batches=3)
    for i in (1, 2, 3):
        reg.create(i, ["A"])
        await reg.mark_complete(i)

    reg.create(4, ["A"])  # over cap → drop the oldest completed (batch 1)

    assert reg.snapshot(1) is None
    assert reg.snapshot(4) is not None
    assert reg.snapshot(2) is not None


def test_never_evicts_incomplete_batches():
    reg = BatchRegistry(max_batches=2)
    reg.create(1, ["A"])
    reg.create(2, ["A"])
    reg.create(3, ["A"])  # over cap but nothing completed → all retained

    assert all(reg.snapshot(i) is not None for i in (1, 2, 3))


async def test_updates_to_unknown_batch_or_item_are_noops():
    reg = BatchRegistry()
    reg.create(1, ["A"])
    await reg.mark_succeeded(99, "A", pitch_id=1)  # unknown batch
    await reg.mark_succeeded(1, "ZZZ", pitch_id=1)  # unknown item
    snap = reg.snapshot(1)
    assert snap.succeeded == 0
