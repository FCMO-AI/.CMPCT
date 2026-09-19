from __future__ import annotations

import threading
import time

import pytest

from cmpct._ordered_pull import ordered_worker_iter


def test_ordered_worker_iter_preserves_canonical_order() -> None:
    def work(value: int) -> int:
        # Later indices finish first; observation must still follow input order.
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
        except BaseException as exc:  # pragma: no cover - diagnostic on assertion failure
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


def test_ordered_worker_iter_observes_lowest_submitted_failure_first() -> None:
    def work(value: int) -> int:
        if value in (1, 2):
            raise ValueError(f"boom-{value}")
        return value

    iterator = ordered_worker_iter(work, [0, 1, 2, 3], 3)
    assert next(iterator) == 0
    with pytest.raises(ValueError, match="boom-1"):
        next(iterator)
