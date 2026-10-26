"""O173-S1: preregistered O169 shared-LRU scan-thrash oracle.

A green test may confirm a NEGATIVE decoded-work tradeoff. Only source-exact
CMPCT.read / cache admission is exercised; mocked VZIP reconstruction does
not measure codec time, physical RSS, or full-product read performance.
See docs/v031-research/2026-10-26-o173-cache-scan-prereg.md.
"""
from collections import OrderedDict
import threading

import pytest
from cmpct import reader


@pytest.mark.parametrize("working_set,second_pass_total_decodes", [(8, 8), (9, 18)])
def test_o173_exact_vzip_read_budget_boundary_scan(
    monkeypatch, working_set, second_pass_total_decodes
):
    # Test-only 8-KiB cap, never changing the actual CMPCT class budget.
    # A forward scan with 9 distinct 1-KiB values has no second-pass hits
    # under plain LRU; 8 distinct values should all remain resident.
    receiver = object.__new__(reader.CMPCT)
    receiver.cache = {}
    receiver.vcache = {}
    receiver._cache_lock = threading.Lock()
    receiver._cache_order = OrderedDict()
    receiver._cache_bytes = 0
    receiver._DECODED_CACHE_MAX_BYTES = 8 * 1024
    receiver._DECODED_CACHE_MAX_ENTRIES = 32768
    receiver._blob = lambda index: b""
    receiver._stream = lambda *args: b""
    receiver.recipes = [(i,) for i in range(working_set)]
    receiver.by = {
        f"member-{i}.zip": [
            f"member-{i}.zip",
            reader.K_FILE,
            0,
            0,
            1024,
            None,
            [reader.S_VZIP, i],
        ]
        for i in range(working_set)
    }

    reconstruction_order = []

    def exact_deterministic_rebuild(recipe, blob_reader, stream_reader):
        i = recipe[0]
        reconstruction_order.append(i)
        return bytes([i]) * 1024

    monkeypatch.setattr(reader, "rebuild_vzip", exact_deterministic_rebuild)

    for repetition in range(2):
        for i in range(working_set):
            actual = receiver.read(f"member-{i}.zip")
            assert actual == bytes([i]) * 1024
            assert receiver._cache_bytes == sum(map(len, receiver.cache.values())) + sum(
                map(len, receiver.vcache.values())
            )
            assert receiver._cache_bytes <= 8 * 1024
            assert len(receiver._cache_order) <= 8
        if repetition == 0:
            assert len(reconstruction_order) == working_set

    # Expected negative for an oversized scan: 9 -> 18, versus 8 -> 8.
    assert len(reconstruction_order) == second_pass_total_decodes
    assert receiver._cache_bytes == 8 * 1024
    assert all(x in range(working_set) for x in reconstruction_order)
