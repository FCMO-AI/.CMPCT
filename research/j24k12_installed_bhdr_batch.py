#!/usr/bin/env python3
"""J24K12: source-exact installed Reader transfer of J24K11 native BHDR proof.

This is a SCIENTIFIC ADAPTER, not a product change or crypto range authenticator.
Raw fresh-process A/B includes the Reader constructor and per-query tuple projection.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from j24k11_bhdr_oracle import install_native

NAME = "science.zip"
CASES = ("q1_early", "q1_tail", "q8_mixed", "q64_tail")
SIZES = (64, 512, 4096)
PAIRS = 5  # 10 fresh subprocesses per cell; alternating A/B and B/A.


def digest(b):
    return hashlib.sha256(b).hexdigest()


def queries_for(size, case):
    assert size > 48
    early = (4, 1)
    middle = (size // 2, 1)
    tail = (size - 8, 1)
    if case == "q1_early":
        return [early]
    if case == "q1_tail":
        return [tail]
    if case == "q8_mixed":
        return [tail, middle, early, tail, early, middle, tail, middle]
    if case == "q64_tail":
        return [(size - 1 - (i % 32), 1) for i in range(64)]
    raise ValueError(case)


def make_authentic_archive(root: Path, n: int):
    """Builder's actual r24 signed wire: one ZIP with n valid STORED members."""
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive
    source = root / ("input-" + str(n))
    source.mkdir()
    original = source / NAME
    with zipfile.ZipFile(original, "w") as z:
        for i in range(n):
            info = zipfile.ZipInfo(f"entry-{i:05d}.bin", date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            payload = hashlib.sha256(f"j24k12:{i}".encode()).digest()
            z.writestr(info, payload)
    archive = root / (str(n) + ".cmpct")
    Builder(source, workers=1, reproducible=True).build(archive)
    truth = original.read_bytes()
    assert preflight_archive(archive)["files"] == 1
    with CMPCT(archive) as reader:
        assert reader.read(NAME) == truth
        assert reader.verify() == 1
        assert len(reader.recipes) == 1
        assert len(reader.recipes[0][2]) == n
        assert all(p[1] == zipfile.ZIP_STORED for p in reader.recipes[0][2])
        assert all(reader.read_range(NAME, s, k) == truth[s:s+k]
                   for case in CASES for s, k in queries_for(len(truth), case))
        signed_sha = digest(archive.read_bytes())
    return archive, original, truth, signed_sha


def project_skipped(reader, recipe, start, length):
    """Project exactly skipped, nonmode2 owners to the unchanged J24K11 C ABI.

    No trust in Python bool indexing or unknown methods/modes. Full construction
    and every object's allocation are charged inside each candidate query.
    """
    import zipfile as zf
    _skref, lens, payloads, _sha, _size, _crc = recipe
    end = start + length
    outpos = 0
    rows = []
    proven = {}
    for i, payload in enumerate(payloads):
        if type(lens[i]) is not int or lens[i] < 0:
            raise IOError("invalid signed skeleton length")
        outpos += lens[i]
        if outpos >= end:
            break
        if len(payload) != 6:
            raise IOError("invalid signed payload")
        rawref, method, mode, streamref, csize, level = payload
        if type(csize) is not int or csize < 0:
            raise IOError("invalid signed stream length")
        segend = outpos + csize
        if segend <= start:
            if type(method) is not int or type(mode) is not int:
                raise IOError("invalid signed stream method/mode")
            if method == zf.ZIP_STORED:
                idx, compressed = rawref, 0
            elif method == zf.ZIP_DEFLATED and mode in (0, 1):
                idx, compressed = streamref, int(mode == 0)
            else:
                # Mode2 needs recompression. Preserve the strict installed path.
                return None, None
            if type(idx) is not int or idx < 0 or idx >= len(reader.blobs):
                raise IOError("invalid signed physical owner")
            descriptor = reader.blobs[idx]
            if len(descriptor) != 5 or not all(type(v) is int and v >= 0 for v in descriptor):
                raise IOError("invalid signed physical descriptor")
            off, us, cs, codec, meta = descriptor
            rows.append((off, us, cs, codec, meta, csize, compressed))
            proven[(method, mode, rawref, streamref)] = csize
        outpos = segend
        if outpos >= end:
            break
    return rows, proven


def batch_read_range(reader, name, start, length, native):
    """Temporary per-call proof. No cross-call cache, source reopen or product mutation."""
    from cmpct.codec import S_VZIP, range_vzip
    storage = reader.by[name][6]
    if storage[0] != S_VZIP or length == 0:
        return reader.read_range(name, start, length)
    recipe = reader.recipes[storage[1]]
    size = reader.by[name][4]
    if (type(start) is not int or type(length) is not int or
            start < 0 or length < 0 or start + length > size):
        return reader.read_range(name, start, length)
    try:
        rows, proven = project_skipped(reader, recipe, start, length)
    except (ValueError, TypeError, IndexError, OSError, OverflowError):
        return reader.read_range(name, start, length)
    if rows is None:
        return reader.read_range(name, start, length)
    if not native.scan(reader.mm, rows, reader.record_base):
        return reader.read_range(name, start, length)
    def positive_size(method, mode, rawref, streamref):
        # A positive C proof binds this exact query's signed owner+length to
        # the same mmap. No fresh or persisted cache survives the operation.
        key = (method, mode, rawref, streamref)
        if key not in proven:
            raise IOError("unproved virtual ZIP physical stream")
        return proven[key]
    return range_vzip(recipe, reader._blob, reader._stream, start, length, positive_size)


def rss_mib():
    if sys.platform == "win32":
        return None
    import resource
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value / (1024 * 1024 if sys.platform == "darwin" else 1024)


def worker(args):
    from cmpct.reader import CMPCT
    archive, original, kind, scenario = map(str, args)
    truth = Path(original).read_bytes()
    ranges = queries_for(len(truth), scenario)
    native = None
    if kind == "batch":
        sys.path.insert(0, os.environ["J24K12_NATIVE_PATH"])
        import j24k11_native as native
    wall0 = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    with CMPCT(Path(archive)) as reader:
        opened_wall = time.perf_counter_ns() - wall0
        opened_cpu = time.process_time_ns() - cpu0
        query_wall0 = time.perf_counter_ns()
        query_cpu0 = time.process_time_ns()
        outputs = []
        for start, length in ranges:
            got = (reader.read_range(NAME, start, length) if kind == "control"
                   else batch_read_range(reader, NAME, start, length, native))
            expected = truth[start:start + length]
            if got != expected:
                raise AssertionError(("wrong reader bytes", start, length, got.hex(), expected.hex()))
            outputs.append(got)
        read_wall = time.perf_counter_ns() - query_wall0
        read_cpu = time.process_time_ns() - query_cpu0
    total_wall = time.perf_counter_ns() - wall0
    total_cpu = time.process_time_ns() - cpu0
    result = {
        "strategy": kind, "scenario": scenario, "n_queries": len(ranges),
        "archive_sha256": digest(Path(archive).read_bytes()), "truth_sha256": digest(truth),
        "query_digest": digest(b"".join(outputs)),
        "opened_wall_ns": opened_wall, "opened_cpu_ns": opened_cpu,
        "read_wall_ns": read_wall, "read_cpu_ns": read_cpu,
        "total_wall_ns": total_wall, "total_cpu_ns": total_cpu,
        "peak_rss_mib": rss_mib(),
    }
    print("J24K12_WORKER=" + json.dumps(result, sort_keys=True), flush=True)


def signed_attack(archive, original, native, dest):
    """Reauthenticate a wrong stream size; require the same Reader-level rejection."""
    import msgpack
    from cmpct.codec import FTR, FMAGIC, HDR, MAGIC, VERSION, sha, zc
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive
    wire = archive.read_bytes()
    with CMPCT(archive) as reader:
        physical_base = reader.record_base
        physical_len = HDR.unpack_from(wire)[5]
        physical = wire[physical_base:physical_base + physical_len]
        index = copy.deepcopy(reader.index)
        rid = index["files"][0][6][1]
        recipe = index["recipes"][rid]
        position = len(recipe[2]) // 2
        assert recipe[2][position][1] == zipfile.ZIP_STORED
        recipe[2][position][4] += 1
        recipe[4] += 1
        index["files"][0][4] += 1
        original_flags = HDR.unpack_from(wire)[2]
    packed_index = msgpack.packb(index, use_bin_type=True)
    compressed = zc(packed_index, 12)
    signed = sha(packed_index)
    attack = (HDR.pack(MAGIC, VERSION, original_flags, len(compressed),
                       len(packed_index), len(physical), signed) +
              compressed + physical + compressed +
              FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed),
                       len(packed_index), 0, signed))
    mutant = dest / "signed-mismatch.cmpct"
    mutant.write_bytes(attack)
    try:
        preflight_archive(mutant)
    except Exception as exc:
        preflight_reject = type(exc).__name__
    else:
        preflight_reject = None
    assert preflight_reject is not None, "signed size lie unexpectedly passes preflight"
    verdict = []
    offset = len(original.read_bytes()) - 1
    with CMPCT(mutant) as candidate:
        for method in ("control", "batch"):
            try:
                (candidate.read_range(NAME, offset, 1) if method == "control"
                 else batch_read_range(candidate, NAME, offset, 1, native))
            except Exception as exc:
                verdict.append((method, type(exc).__name__))
            else:
                raise AssertionError("reauthenticated wrong-byte size lie was accepted: " + method)
    return {"signed_mutant_sha256": digest(attack), "preflight_reject": preflight_reject,
            "rejections": verdict}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        return worker(sys.argv[2:])
    # Import the actual installed Reader, not the research checkout's source.
    import cmpct.reader as reader_module
    import cmpct.codec as codec_module
    native, build_dir, build_ns = install_native()
    parent = Path(os.environ.get("J24K12_WORKDIR", tempfile.mkdtemp(prefix="j24k12-")))
    parent.mkdir(parents=True, exist_ok=True)
    cells = []
    source_id = {
        "reader_sha256": digest(Path(reader_module.__file__).read_bytes()),
        "codec_sha256": digest(Path(codec_module.__file__).read_bytes()),
        "c_scanner_sha256": digest(__import__("j24k11_bhdr_oracle").C_SOURCE.encode()),
        "instrument_sha256": digest(Path(__file__).read_bytes())
    }
    env = dict(os.environ, J24K12_NATIVE_PATH=str(build_dir))
    for n in SIZES:
        archive, original, truth, archive_hash = make_authentic_archive(parent, n)
        if n == 64:
            negative = signed_attack(archive, original, native, parent)
        for scenario in CASES:
            observations = {"control": [], "batch": []}
            queries = queries_for(len(truth), scenario)
            qdigest = digest(b"".join(truth[s:s+k] for s, k in queries))
            for i in range(PAIRS):
                order = ("control", "batch") if i % 2 == 0 else ("batch", "control")
                for strategy in order:
                    start = time.perf_counter_ns()
                    command = [sys.executable, str(Path(__file__).resolve()), "--worker",
                               str(archive), str(original), strategy, scenario]
                    p = subprocess.run(command, env=env, text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    outer_ns = time.perf_counter_ns() - start
                    if p.returncode:
                        raise RuntimeError("worker failure: " + p.stdout[-5000:])
                    records = [json.loads(line.split("J24K12_WORKER=", 1)[1])
                               for line in p.stdout.splitlines() if line.startswith("J24K12_WORKER=")]
                    assert len(records) == 1
                    observation = records[0]
                    assert observation["archive_sha256"] == archive_hash
                    assert observation["query_digest"] == qdigest
                    observation["process_wall_ns"] = outer_ns
                    observations[strategy].append(observation)
            median = {
                strategy: {
                    metric: statistics.median(p[metric] for p in rows)
                    for metric in ("opened_wall_ns", "opened_cpu_ns", "read_wall_ns", "read_cpu_ns",
                                   "total_wall_ns", "total_cpu_ns", "process_wall_ns")
                } for strategy, rows in observations.items()
            }
            ratio = {k: median["control"][k] / max(1, median["batch"][k])
                     for k in ("total_wall_ns", "total_cpu_ns", "read_wall_ns", "read_cpu_ns",
                               "process_wall_ns")}
            cell = {"n_streams": n, "scenario": scenario, "archive_sha256": archive_hash,
                    "truth_sha256": digest(truth), "queries_sha256": digest(json.dumps(queries).encode()),
                    "query_digest": qdigest, "archive_bytes": archive.stat().st_size,
                    "observations": observations, "median": median, "ratio": ratio}
            cells.append(cell)
            print("J24K12_CELL=" + json.dumps({k:v for k,v in cell.items() if k != "observations"},
                                               sort_keys=True), flush=True)
    decisive = [c for c in cells if c["n_streams"] >= 512 and c["scenario"] == "q64_tail"]
    min_ratio = min(c["ratio"][k] for c in decisive for k in ("total_wall_ns", "total_cpu_ns"))
    result = {
        "schema": "j24k12-authentic-installed-r24-v1",
        "class": "installed_scientific_adapter_not_published_product",
        "source": source_id,
        "platform": platform.platform(), "python": sys.version.split()[0],
        "native_build_ns": build_ns, "native_extension_path": str(build_dir),
        "cell_count": len(cells), "observations": len(cells) * PAIRS * 2,
        "signed_attack": negative, "cells": cells,
        "min_decisive_total_ratio": min_ratio,
        "decision": ("INSTALLED_BATCH_HEADROOM" if min_ratio >= 1.20
                     else "INSTALLED_BATCH_HEADROOM_NOT_PROVEN")
    }
    out = Path(os.environ.get("J24K12_OUT", "j24k12-results.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("J24K12_RESULT=" + json.dumps({k:v for k,v in result.items()
                                         if k not in ("cells", "source")}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
