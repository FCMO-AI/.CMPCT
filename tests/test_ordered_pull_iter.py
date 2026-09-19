from __future__ import annotations

import threading
import time

import pytest

from cmpct._ordered_pull import ordered_worker_iter


def test_ordered_worker_iter_preserves_canonical_order() -> None:
    def work(value: int) -> int:
        time.sleep((5 - value) * 0.002)
        return value * 10

    assert list(ordered_worker_iter(work, list(range(6)), 3)) == [0, 10, 20, 30, 40, 50]


def test_ordered_worker_iter_bounds_claim_window_until_consumed() -> None:
    first_release = threading.Event()
    started: list[int] = []
    lock = threading.Lock()

    def work(value: int) -> int:
        with lock:
            started.append(value)
        if value == 0:
            assert first_release.wait(timeout=2)
        return value

    iterator = ordered_worker_iter(work, list(range(8)), 3)
    observed: list[int] = []
    error: list[BaseException] = []

    def consume_first() -> None:
        try:
            observed.append(next(iterator))
        except BaseException as exc:  # pragma: no cover
            error.append(exc)

    thread = threading.Thread(target=consume_first)
    thread.start()
    deadline = time.monotonic() + 2
    while True:
        with lock:
            claimed = list(started)
        if len(claimed) >= 3 or time.monotonic() >= deadline:
            break
        time.sleep(0.005)
    assert sorted(claimed) == [0, 1, 2]
    time.sleep(0.02)
    with lock:
        assert sorted(started) == [0, 1, 2]
    first_release.set()
    thread.join(timeout=2)
    assert not error
    assert observed == [0]
    iterator.close()


def test_ordered_worker_iter_closes_claims_when_later_worker_fails() -> None:
    first_release = threading.Event()
    failed = threading.Event()
    started: list[int] = []
    lock = threading.Lock()

    def work(value: int) -> int:
        with lock:
            started.append(value)
        if value == 0:
            assert first_release.wait(timeout=2)
        if value == 2:
            failed.set()
            raise ValueError("boom-2")
        return value

    iterator = ordered_worker_iter(work, [0, 1, 2, 3, 4], 3)
    observed: list[int] = []
    thread = threading.Thread(target=lambda: observed.append(next(iterator)))
    thread.start()
    assert failed.wait(timeout=2)
    first_release.set()
    thread.join(timeout=2)
    assert observed == [0]
    # Failure at already-submitted index 2 closes the gate before consuming index 0 can submit index 3.
    with lock:
        assert 3 not in started and 4 not in started
    assert next(iterator) == 1
    with pytest.raises(ValueError, match="boom-2"):
        next(iterator)


def test_ordered_worker_iter_observes_lowest_submitted_failure_first() -> None:
    def work(value: int) -> int:
        if value in (1, 2):
            raise ValueError(f"boom-{value}")
        return value

    iterator = ordered_worker_iter(work, [0, 1, 2, 3], 3)
    assert next(iterator) == 0
    with pytest.raises(ValueError, match="boom-1"):
        next(iterator)
