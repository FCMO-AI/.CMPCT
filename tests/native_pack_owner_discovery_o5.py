#!/usr/bin/env python3
"""Preregistered O5: native S_PACK grouping discovery, real product and independent wire."""
from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_PACK, CODEC_ZSTD

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from native_pack_batch_abi import Request, open_native, map_paths, serial, batch, load_library, source_bytes

GOLDEN = ROOT / "tests/conformance/v24-pack.json"


def owner_query(lib, handle, index):
    out = ctypes.c_size_t(983765)
    status = lib.cmpct_entry_pack_owner(handle, index, ctypes.byref(out))
    return status, out.value


def fixed_goldens(lib, home):
    verdicts = []
    for v in json.loads(GOLDEN.read_text())["vectors"]:
        raw = base64.b64decode(v["archive_base64"], validate=True)
        assert hashlib.sha256(raw).hexdigest() == v["archive_sha256"]
        path = home / (v["name"] + ".cmpct")
        path.write_bytes(raw)
        handle = open_native(lib, path)
        try:
            paths = map_paths(lib, handle)
            statuses = [owner_query(lib, handle, i) for i in paths.values()]
            if v["physical_codec"] == CODEC_ZSTD:
                assert len({owner for status, owner in statuses if status == 0}) == 1, statuses
                assert all(status == 0 for status, _ in statuses), statuses
            else:
                assert all((status, owner) == (-7, 0) for status, owner in statuses), statuses
            verdicts.append({"source": v["name"], "sha256": v["archive_sha256"],
                             "entry_statuses": statuses})
        finally:
            lib.cmpct_close(handle)
    return verdicts


def real_builder(lib, home):
    root = home / "source"
    root.mkdir()
    for i in range(512):
        (root / f"entry-{i:05d}.txt").write_bytes(source_bytes(i))
    (root / "subfolder").mkdir()
    # Deterministic high-entropy non-PACK control: preserve source fingerprint across runners.
    # Do not let unrelated os.urandom() change the product evidence input every activation.
    nonpack_bytes = b"".join(
        hashlib.sha256(f"native-owner-o5-nonpack-{i}".encode()).digest()
        for i in range(2200)
    )[:70000]
    (root / "subfolder" / "nonpack.bin").write_bytes(nonpack_bytes)
    archive = home / "real.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive)
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    handle = open_native(lib, archive)
    try:
        paths = map_paths(lib, handle)
        groups = {}
        rejected = {}
        first_pass = []
        for path, entry_index in paths.items():
            t0 = time.perf_counter_ns()
            status, owner = owner_query(lib, handle, entry_index)
            first_pass.append((time.perf_counter_ns() - t0) / 1000)
            if status == 0:
                groups.setdefault(owner, []).append((path, entry_index))
            else:
                rejected[path] = (status, owner)
        assert len(groups) >= 2, {"groups": list(groups), "rejected": rejected}
        assert any(len(g) >= 256 for g in groups.values()), {k: len(v) for k, v in groups.items()}
        assert all(status == -7 and owner == 0 for status, owner in rejected.values())
        assert "subfolder/nonpack.bin" in rejected

        # Strong differently-rooted oracle: query groups FIRST using only native ABI,
        # then compare grouping to the Python Reader's independently decoded owner map.
        with CMPCT(archive) as parsed:
            physical = {row[0]: int(row[6][1]) for row in parsed.files
                        if row[1] == 0 and row[6] and row[6][0] == S_PACK
                        and int(parsed.blobs[int(row[6][1])][3]) == CODEC_ZSTD}
            for rows in groups.values():
                assert len({physical[path] for path, _ in rows}) == 1
            assert len({physical[rows[0][0]] for rows in groups.values()}) == len(groups)
        selected = max(groups.values(), key=len)
        rows = selected[:256]
        requests = [(idx, 17, 64) for _, idx in rows]
        want = b"".join((root / path).read_bytes()[17:81] for path, _ in rows)
        status, got, written = batch(lib, handle, requests)
        assert (status, written, got) == (0, len(want), want)
        assert serial(lib, handle, requests) == want
        # Mixed physical owners must remain a fatal, no-write failure.
        other = next(r for r in groups.values() if r is not selected)
        bad = [requests[0], (other[0][1], 17, 64)]
        st, untouched, n = batch(lib, handle, bad)
        assert st == -7 and n == 0 and untouched == bytes([0xA5]) * 128, (st, n)
        # C ABI invalid calls: always fail-zero on valid output pointer.
        assert owner_query(lib, handle, lib.cmpct_entry_count(handle) + 9) == (-6, 0)
        assert owner_query(lib, None, rows[0][1]) == (-1, 0)
        assert lib.cmpct_entry_pack_owner(handle, rows[0][1], None) == -1
        times = []
        for _ in range(7):
            t0 = time.perf_counter_ns()
            for _, i in paths.items():
                owner_query(lib, handle, i)
            times.append((time.perf_counter_ns() - t0) / 1e6)
        return {
            "archive_sha256": archive_sha,
            "native_groups": {str(o): len(rows) for o, rows in groups.items()},
            "fallback_entries": sorted(rejected),
            "independent_python_owner_parity": True,
            "batch_member_count": len(requests),
            "batch_output_sha256": hashlib.sha256(got).hexdigest(),
            "first_pass_query_median_us": statistics.median(first_pass),
            "full_enumeration_ms": times,
            "full_enumeration_median_ms": statistics.median(times),
        }
    finally:
        lib.cmpct_close(handle)


def main():
    lib = load_library()
    lib.cmpct_entry_pack_owner.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    lib.cmpct_entry_pack_owner.restype = ctypes.c_int
    with tempfile.TemporaryDirectory(prefix="cmpct-owner-o5-") as td:
        home = Path(td)
        fixed = fixed_goldens(lib, home)
        product = real_builder(lib, home)
    result = {"schema": "cmpct-native-owner-o5-v1", "exact_native_metadata": True,
              "fixed_wire": fixed, "product": product, "status": "O5_PASS"}
    assert len(sys.argv) == 2
    Path(sys.argv[1]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
