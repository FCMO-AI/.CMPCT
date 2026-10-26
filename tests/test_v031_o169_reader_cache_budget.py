"""O169: deterministic and concurrent falsifiers of shared decoded-cache admission.

The tests assert retained payload, not total RSS or transient caller allocations.
They deliberately do not weaken existing Reader/Builder/equality tests.
"""
from __future__ import annotations

import concurrent.futures
import threading
from collections import OrderedDict

from cmpct import reader


def _bare_cache():
    # Minimal Reader receiver: exercise actual class methods without mmap/native fixture noise.
    obj = object.__new__(reader.CMPCT)
    obj.cache = {}
    obj.vcache = {}
    obj._cache_lock = threading.Lock()
    obj._cache_order = OrderedDict()
    obj._cache_bytes = 0
    return obj


def _assert_accounting(obj):
    payload = sum(map(len, obj.cache.values())) + sum(map(len, obj.vcache.values()))
    assert obj._cache_bytes == payload
    assert obj._cache_bytes <= obj._DECODED_CACHE_MAX_BYTES
    assert len(obj._cache_order) == len(obj.cache) + len(obj.vcache)
    assert len(obj._cache_order) <= obj._DECODED_CACHE_MAX_ENTRIES
    assert set(obj._cache_order) == (
        {(0, key) for key in obj.cache} | {(1, key) for key in obj.vcache}
    )


def test_mixed_namespace_eviction_and_exact_cache_hits():
    obj = _bare_cache()
    mib = 1 << 20
    for i in range(80):
        kind = i % 2
        raw = bytes([i]) * mib
        assert obj._retain_decoded(kind, i, raw) == raw
        _assert_accounting(obj)
    assert obj._cache_bytes == 64 * mib
    assert obj._cached_decoded(0, 0) is None
    assert obj._cached_decoded(1, 1) is None
    assert obj._cached_decoded(0, 78) == bytes([78]) * mib
    # Make the oldest surviving item hot: a subsequent insert must not evict it.
    assert obj._cached_decoded(0, 16) == bytes([16]) * mib
    obj._retain_decoded(1, 999, b"next" * (mib // 4))
    assert obj._cached_decoded(0, 16) == bytes([16]) * mib
    assert obj._cached_decoded(1, 17) is None
    _assert_accounting(obj)


def test_oversized_result_does_not_evict_or_remain_retained():
    obj = _bare_cache()
    obj._retain_decoded(0, 1, b"small")
    oversized = b"X" * (obj._DECODED_CACHE_MAX_BYTES + 1)
    assert obj._retain_decoded(1, 2, oversized) is oversized
    assert obj._cached_decoded(1, 2) is None
    assert obj._cached_decoded(0, 1) == b"small"
    _assert_accounting(obj)


def test_empty_payload_count_is_bounded_and_lru_refreshes():
    obj = _bare_cache()
    cap = obj._DECODED_CACHE_MAX_ENTRIES
    for idx in range(cap + 3):
        obj._retain_decoded(idx % 2, idx, b"")
    assert obj._cached_decoded(0, 0) is None
    assert obj._cached_decoded(1, cap + 2) == b""
    assert obj._cache_bytes == 0
    _assert_accounting(obj)


def test_concurrent_admit_lookup_accounting_and_exactness():
    obj = _bare_cache()

    def worker(i):
        kind = i % 2
        idx = i // 2
        raw = bytes([idx % 251]) * (128 * 1024)
        assert obj._retain_decoded(kind, idx, raw) == raw
        found = obj._cached_decoded(kind, idx)
        # Another worker may legitimately evict a result before this lookup.
        assert found is None or found == raw

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(worker, range(1200)))
    _assert_accounting(obj)


def test_actual_vzip_read_path_returns_exact_values_and_reuses_small_entries(monkeypatch):
    obj = _bare_cache()
    obj.by = {
        "a.zip": ["a.zip", reader.K_FILE, 0, 0, 7, None, [reader.S_VZIP, 0]],
        "b.zip": ["b.zip", reader.K_FILE, 0, 0, 7, None, [reader.S_VZIP, 1]],
    }
    obj.recipes = [[b"ZIPDATA"], [b"DATAZIP"]]
    calls = []
    def rebuild(recipe, *args):
        calls.append(recipe[0])
        return recipe[0]
    monkeypatch.setattr(reader, "rebuild_vzip", rebuild)
    assert obj.read("a.zip") == b"ZIPDATA"
    assert obj.read("a.zip") == b"ZIPDATA"
    assert obj.read("b.zip") == b"DATAZIP"
    assert calls == [b"ZIPDATA", b"DATAZIP"]
    _assert_accounting(obj)
