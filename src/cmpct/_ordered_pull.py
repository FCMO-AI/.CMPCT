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
    lock, and publish into fixed result slots. The first worker failure closes the
    claim gate so already-running calls may unwind but no new candidate work is
    started. ``future.result()`` propagates the original worker exception.
    """
    count = len(items)
    if count == 0:
        return []
    worker_count = max(1, min(int(workers), count))
    if worker_count == 1:
        return [fn(item) for item in items]

    results: list[_R | None] = [None] * count
    next_index = 0
    aborted = False
    claim_lock = threading.Lock()

    def pull() -> None:
        nonlocal next_index, aborted
        while True:
            with claim_lock:
                if aborted or next_index >= count:
                    return
                index = next_index
                next_index = index + 1
            try:
                result = fn(items[index])
            except BaseException:
                with claim_lock:
                    aborted = True
                raise
            results[index] = result

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=worker_count, thread_name_prefix="cmpct-encode"
    ) as pool:
        futures = [pool.submit(pull) for _ in range(worker_count)]
        for future in futures:
            future.result()

    return cast(list[_R], results)
