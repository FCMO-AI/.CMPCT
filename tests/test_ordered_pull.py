from __future__ import annotations

import threading
import time

import pytest

from cmpct._ordered_pull import ordered_worker_pull


def test_empty_and_single_worker_paths_are_exact():
    assert ordered_worker_pull(lambda x: x * 2, [], 8) == []
    seen = []
    assert ordered_worker_pull(lambda x: seen.append(x) or x * 2, [3], 8) == [6]
    assert seen == [3]


def test_fewer_items_than_workers_preserves_canonical_order():
    def encode(value: int) -> int:
        time.sleep((4 - value) * 0.002)
        return value * 10

    assert ordered_worker_pull(encode, [1, 2, 3], 32) == [10, 20, 30]


def test_parallel_completion_order_cannot_reorder_results():
    completed = []
    lock = threading.Lock()
    release_zero = threading.Event()

    def encode(value: int) -> int:
        if value == 0:
            assert release_zero.wait(timeout=2)
        with lock:
            completed.append(value)
            if value == 1:
                release_zero.set()
        return value

    expected = list(range(8))
    assert ordered_worker_pull(encode, expected, 4) == expected
    assert completed.index(1) < completed.index(0)


def test_worker_concurrency_never_exceeds_requested_bound():
    active = peak = 0
    lock = threading.Lock()

    def encode(value: int) -> int:
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.002)
        with lock:
            active -= 1
        return value

    items = list(range(80))
    assert ordered_worker_pull(encode, items, 5) == items
    assert 1 < peak <= 5


def test_worker_exception_propagates_and_stops_new_claims():
    workers = 4
    first_wave = threading.Barrier(workers)
    started = []
    lock = threading.Lock()

    def encode(value: int) -> int:
        with lock:
            started.append(value)
        first_wave.wait(timeout=2)
        if value == 0:
            raise RuntimeError("sentinel encode failure")
        time.sleep(0.01)
        return value

    with pytest.raises(RuntimeError, match="sentinel encode failure"):
        ordered_worker_pull(encode, list(range(40)), workers)
    assert sorted(started) == list(range(workers))


def test_multiple_inflight_failures_raise_lowest_canonical_index():
    first_wave = threading.Barrier(2)
    one_failed = threading.Event()

    def encode(value: int) -> int:
        first_wave.wait(timeout=2)
        if value == 1:
            one_failed.set()
            raise RuntimeError("index one failed first")
        assert value == 0
        assert one_failed.wait(timeout=2)
        raise RuntimeError("index zero is canonical")

    with pytest.raises(RuntimeError, match="index zero is canonical"):
        ordered_worker_pull(encode, [0, 1], 2)


@pytest.mark.parametrize("workers", [1, 2, 8])
def test_worker_counts_preserve_ordered_semantics(workers: int):
    items = list(range(41))
    expected = [x * x for x in items]
    assert ordered_worker_pull(lambda x: x * x, items, workers) == expected


def test_repeated_parallel_runs_are_deterministic():
    items = list(range(97))
    expected = [x * x for x in items]
    for _ in range(20):
        assert ordered_worker_pull(lambda x: x * x, items, 7) == expected
