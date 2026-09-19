from __future__ import annotations

"""Bounded ordered parallel mapping for Builder candidate encoding.

The primitives keep only bounded scheduling state while preserving input order.
They intentionally live below Builder policy so product materialization can choose
whether it needs a retained result list or can consume results incrementally without
changing archive ordering or codec semantics.

This module is release-critical product code: changes to its scheduling semantics
must be covered by the exact-head release authority, not only a mechanism-local A/B.
"""

import concurrent.futures
import threading
from collections.abc import Callable, Iterator, Sequence
from typing import TypeVar, cast

_T = TypeVar("_T")
_R = TypeVar("_R")


def ordered_worker_iter(fn: Callable[[_T], _R], items: Sequence[_T], workers: int) -> Iterator[_R]:
    """Yield mapped results in canonical order with at most O(workers) results resident.

    A fixed initial window is submitted. Each canonical result is awaited and yielded
    before one replacement item is submitted, so a slow early item cannot create an
    unbounded completed-result backlog. Any submitted worker failure closes the claim
    gate immediately; already-submitted calls may unwind, and exceptions are still
    observed in canonical index order. This matches the retained mapper's material
    failure boundary while allowing callers to release each successful result promptly.
    """
    count = len(items)
    if count == 0:
        return
    worker_count = max(1, min(int(workers), count))
    if worker_count == 1:
        for item in items:
            yield fn(item)
        return

    abort_event = threading.Event()

    def close_on_failure(future: concurrent.futures.Future[_R]) -> None:
        if future.cancelled():
            return
        try:
            failed = future.exception() is not None
        except concurrent.futures.CancelledError:
            return
        if failed:
            abort_event.set()

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=worker_count, thread_name_prefix="cmpct-encode"
    ) as pool:
        futures: dict[int, concurrent.futures.Future[_R]] = {}

        def submit(index: int) -> None:
            future = pool.submit(fn, items[index])
            future.add_done_callback(close_on_failure)
            futures[index] = future

        for index in range(worker_count):
            submit(index)
        next_submit = worker_count
        for index in range(count):
            future = futures.pop(index)
            try:
                result = future.result()
            except BaseException:
                abort_event.set()
                for pending in futures.values():
                    pending.cancel()
                raise
            yield result
            if next_submit < count and not abort_event.is_set():
                submit(next_submit)
                next_submit += 1


def ordered_worker_pull(fn: Callable[[_T], _R], items: Sequence[_T], workers: int) -> list[_R]:
    """Map *fn* over *items* with bounded futures and ordered retained results.

    Workers claim canonical indices under a tiny lock, execute ``fn`` outside the
    lock, and publish into fixed result slots. Failure closes the claim gate while
    holding the same lock used for claims, so once a failure is recorded no later
    candidate can be claimed. Already-claimed calls may unwind. If several such
    calls fail, the lowest canonical-index exception is raised, matching ordered
    ``Executor.map`` result observation.
    """
    count = len(items)
    if count == 0:
        return []
    worker_count = max(1, min(int(workers), count))
    if worker_count == 1:
        return [fn(item) for item in items]

    results: list[_R | None] = [None] * count
    failures: list[tuple[int, BaseException]] = []
    next_index = 0
    abort_event = threading.Event()
    claim_lock = threading.Lock()

    def pull() -> None:
        nonlocal next_index
        while True:
            with claim_lock:
                if abort_event.is_set() or next_index >= count:
                    return
                index = next_index
                next_index = index + 1
            try:
                result = fn(items[index])
            except BaseException as exc:
                with claim_lock:
                    failures.append((index, exc))
                    abort_event.set()
                return
            results[index] = result

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=worker_count, thread_name_prefix="cmpct-encode"
    ) as pool:
        futures = [pool.submit(pull) for _ in range(worker_count)]
        for future in futures:
            future.result()

    if failures:
        raise min(failures, key=lambda item: item[0])[1]
    return cast(list[_R], results)
