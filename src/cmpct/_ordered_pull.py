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
    """Map *fn* over *items* with at most ``min(workers, len(items))`` futures.

    Workers claim canonical indices under a tiny lock, execute ``fn`` outside the
    lock, and publish into fixed result slots. Calling ``future.result()`` keeps
    worker exceptions visible to the caller rather than silently losing them.
    """
    count = len(items)
    if count == 0:
        return []
    worker_count = max(1, min(int(workers), count))
    if worker_count == 1:
        return [fn(item) for item in items]

    results: list[_R | None] = [None] * count
    next_index = 0
    claim_lock = threading.Lock()

    def pull() -> None:
        nonlocal next_index
        while True:
            with claim_lock:
                index = next_index
                if index >= count:
                    return
                next_index = index + 1
            results[index] = fn(items[index])

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=worker_count, thread_name_prefix="cmpct-encode"
    ) as pool:
        futures = [pool.submit(pull) for _ in range(worker_count)]
        for future in futures:
            future.result()

    return cast(list[_R], results)
