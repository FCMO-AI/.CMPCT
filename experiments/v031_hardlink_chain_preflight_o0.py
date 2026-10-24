#!/usr/bin/env python3
"""O0 only: source-exact installed CMPCT strict-preflight hardlink-chain cost court.

No threshold gate: preserve raw timing, provenance and full-wire authenticated inputs.
Source-bound prediction: chain aliases repeatedly walk old targets; star aliases do not.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import tempfile
import time

import msgpack

from cmpct.builder import Builder
from cmpct.codec import FMAGIC, FTR, HDR, K_HARDLINK, MAGIC, sha, zc, zd
from cmpct.validation import ValidationError, preflight_archive


def checked_source_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def make_signed_alias_archive(source: Path, destination: Path, count: int, shape: str) -> dict:
    original = source.read_bytes()
    magic, version, flags, compressed_size, raw_size, data_size, digest = HDR.unpack_from(original)
    assert magic == MAGIC and version == 24
    plain = zd(original[HDR.size:HDR.size + compressed_size], raw_size)
    assert sha(plain) == digest
    index = msgpack.unpackb(plain, raw=False)
    assert len(index["files"]) == 1
    owner = index["files"][0]
    assert owner[0] == "a0000000.bin"
    rows = [owner]
    previous = owner[0]
    for i in range(count):
        path = f"z{i:08d}.bin"
        target = previous if shape == "chain" else owner[0]
        assert len(path) == len(target) == len(owner[0])
        rows.append([path, K_HARDLINK, owner[2], owner[3], owner[4], None, [target]])
        previous = path
    index["files"] = rows
    encoded_index = msgpack.packb(index, use_bin_type=True)
    compressed_index = zc(encoded_index, 12)
    new_digest = sha(encoded_index)
    physical = original[HDR.size + compressed_size:HDR.size + compressed_size + data_size]
    assert len(physical) == data_size
    destination.write_bytes(
        HDR.pack(MAGIC, version, flags, len(compressed_index), len(encoded_index), data_size, new_digest)
        + compressed_index + physical + compressed_index
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed_index), len(encoded_index), 0, new_digest)
    )
    wire = destination.read_bytes()
    assert wire[HDR.size + len(compressed_index):HDR.size + len(compressed_index) + data_size] == physical
    assert wire[HDR.size:HDR.size + len(compressed_index)] == wire[-FTR.size - len(compressed_index):-FTR.size]
    assert HDR.unpack_from(wire)[-1] == new_digest
    return {
        "archive_sha256": hashlib.sha256(wire).hexdigest(),
        "complete_stored_bytes": len(wire),
        "index_plain_bytes": len(encoded_index),
        "index_compressed_bytes": len(compressed_index),
        "physical_bytes": len(physical),
    }


def main() -> None:
    head = checked_source_head()
    sizes = (128, 512, 2048, 4096)
    repeats = 5
    output = {
        "court": "v031-hardlink-chain-preflight-O0",
        "class": "research/oracle only; not full-product benchmark",
        "source_head": head,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "counts": list(sizes),
        "repetitions": repeats,
        "cases": {},
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-hl-chain-o0-") as td:
        root = Path(td)
        source_tree = root / "input"
        source_tree.mkdir()
        (source_tree / "a0000000.bin").write_bytes(b"BOUNDARY-EXACT-OWNER" * 8)
        seed = root / "source.cmpct"
        Builder(source_tree, workers=1, reproducible=True).build(seed)
        for n in sizes:
            paths = {}
            manifests = {}
            for shape in ("chain", "star"):
                path = root / f"aliases-{shape}-{n}.cmpct"
                manifests[shape] = make_signed_alias_archive(seed, path, n, shape)
                paths[shape] = path
                info = preflight_archive(path)
                assert info["files"] == n + 1, (shape, n, info)
            raw_ns = {"chain": [], "star": []}
            for repeat in range(repeats):
                order = ("chain", "star") if repeat % 2 == 0 else ("star", "chain")
                for shape in order:
                    t0 = time.perf_counter_ns()
                    got = preflight_archive(paths[shape])
                    elapsed = time.perf_counter_ns() - t0
                    assert got["files"] == n + 1
                    raw_ns[shape].append(elapsed)
            median = {k: statistics.median(v) for k, v in raw_ns.items()}
            output["cases"][str(n)] = {
                "wire": manifests,
                "raw_preflight_ns": raw_ns,
                "median_preflight_ns": median,
                "chain_over_star_median": round(median["chain"] / median["star"], 4),
                "predicted_chain_pointer_edges": n * (n + 1) // 2,
                "predicted_star_pointer_edges": n,
            }
            print(
                f"O0_COUNT={n} chain_ns={median['chain']:.0f} star_ns={median['star']:.0f} "
                f"chain_star_ratio={median['chain']/median['star']:.3f} "
                f"all_preflights_valid=True", flush=True
            )
    output["ru_maxrss_platform_units"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    output_path = Path(os.environ.get("O0_EVIDENCE_FILE", "hardlink-chain-o0-evidence.json"))
    output_path.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"O0_EVIDENCE_PATH={output_path} SOURCE_HEAD={head}", flush=True)


if __name__ == "__main__":
    main()
