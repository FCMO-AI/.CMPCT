from __future__ import annotations

"""Bounded ordered parallel mapping for Builder candidate encoding.

The primitive keeps only O(workers) futures resident while preserving input order.
It intentionally lives below Builder policy so the product patch can replace eager
Executor.map submission without changing archive ordering or codec semantics.
"""

import concurrent.futures
import threading
from collections.abc import Callable, Sequence
from typing import TypeVar, cast

_T = TypeVar("_T")
_R = TypeVar("_R")


def ordered_worker_pull(fn: Callable[[_T], _R], items: Sequence[_T], workers: int) -> list[_R]:
    """Map *fn* over *items* with bounded futures and ordered results.

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
                # Failure publication and claim closure share the claim lock. This removes the
                # check/set race where another worker could observe an open gate after this call
                # had already failed but before abort_event.set() became visible.
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
