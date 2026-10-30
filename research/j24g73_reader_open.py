#!/usr/bin/env python3
"""J24G73: research-only, source-attested full Reader-open A/B on physical r24 journals.

No shipping Reader modification. The subclass changes only the journal application
boundary during a scientific run; both variants read identical archive bytes.
"""
from __future__ import annotations

import copy
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc

import msgpack

from cmpct import _xattrs, transactions as tx
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.journal_replay import JournalReplayAdmissionError
from cmpct.validation import preflight_archive
from j24g60_single_delta_chain_court import footer_chain, sha256_file
from j24g62_crossgen_rename_oracle import read_wire
from j24g64_mixed_fsmeta_oracle import factored, reference, fingerprint

ROOT = Path(__file__).resolve().parents[1]
PARENT = "41cd7f88d9fede55a495f36e78126b26eff85880"
PREREG = "47098cb201bf2424a436d197d7bd09162d872b78"
EXPECTED_BLOBS = {
    "src/cmpct/reader.py": "29a8be64f3acfb027750351c6a567fd82cf7dc97",
    "src/cmpct/journal_replay.py": "03743ca2a06c022c2ec64243a90fe373cf91e899",
    "research/j24g64_mixed_fsmeta_oracle.py": "7657a41d11f2b3c8136c0b69cfe62401f9b19ccb",
}
KEY = "com.fcmo.cmpct.j24g73" if sys.platform == "darwin" else "user.cmpct_j24g73"
DEPTH = 63
BLOCKS = 8


def attest():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for ancestor in (PARENT, PREREG):
        assert subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, head],
                              cwd=ROOT, stdout=subprocess.DEVNULL).returncode == 0, (ancestor, head)
    ids = {}
    for path, expected in EXPECTED_BLOBS.items():
        sha = subprocess.check_output(["git", "rev-parse", "HEAD:" + path],
                                      cwd=ROOT, text=True).strip()
        assert sha == expected, (path, sha, expected)
        ids[path] = sha
    import cmpct.reader as installed
    import cmpct.journal_replay as installed_replay
    for relative, module in (("src/cmpct/reader.py", installed),
                             ("src/cmpct/journal_replay.py", installed_replay)):
        assert Path(module.__file__).read_bytes().replace(b"\r\n", b"\n") == (
            ROOT / relative).read_bytes().replace(b"\r\n", b"\n"), ("installed source drift", relative)
    return {"head": head, "parent": PARENT, "prereg": PREREG, "source_blobs": ids}


class FactoredCMPCT(CMPCT):
    """Same inherited Reader except batch application of already-decoded signed deltas.

    This is NOT a proposed production patch: it provides an experimental upper
    bound, with the unchanged conservative #808 admission/fallback and signatures.
    """
    def _index_from_footer(self, footer_pos: int):
        chain = []
        pos, depth, seen = footer_pos, 0, set()
        while pos and pos not in seen:
            seen.add(pos)
            generation = self._decode_generation_payload(pos)
            if generation is None:
                return None
            kind, payload, prev = generation
            if kind == 0:
                index = msgpack.unpackb(payload, raw=False)
                if chain:
                    try:
                        index, route = factored(index, list(reversed(chain)))
                        self._research_route = route
                    except JournalReplayAdmissionError as exc:
                        raise IOError("unsupported committed r24 journal operation: " + str(exc)) from exc
                    except (ValueError, TypeError, KeyError, IndexError):
                        return None
                else:
                    self._research_route = "checkpoint"
                return index, depth
            if kind != 1:
                return None
            chain.append(msgpack.unpackb(payload, raw=False))
            depth += 1
            pos = prev
        return None


def xattr_projection(index):
    rows = index["files"]
    out = {}
    for pos, keys in (index.get("fsmeta") or {}).get("xattrs", []):
        assert type(pos) is int and 0 <= pos < len(rows)
        out[rows[pos][0]] = {key: val for key, val in keys}
    return out


def native_attr(path, key):
    try:
        return _xattrs.getxattr(path, key, follow_symlinks=False)
    except OSError as exc:
        if exc.errno in {errno.ENODATA, getattr(errno, "ENOATTR", errno.ENODATA)}:
            return None
        raise


def verify_pair(path, expected, tags, strict_xattrs):
    physical = sha256_file(path)
    base, deltas = read_wire(path)
    assert len(deltas) == DEPTH
    expected_index = reference(base, deltas)
    oracle_index, route = factored(base, deltas)
    assert route == "factored", ("candidate not admitted", route)
    assert oracle_index == expected_index
    assert fingerprint(oracle_index) == fingerprint(expected_index)
    with CMPCT(path) as original, FactoredCMPCT(path) as candidate:
        assert candidate._research_route == "factored"
        assert original.delta_depth == candidate.delta_depth == DEPTH
        assert original.latest_footer_pos == candidate.latest_footer_pos
        assert original.index == candidate.index == expected_index
        assert (msgpack.packb(original.index, use_bin_type=True) ==
                msgpack.packb(candidate.index, use_bin_type=True))
        assert set(original.by) == set(candidate.by) == set(expected)
        assert original.verify() == candidate.verify() == len(expected)
        for name, raw in expected.items():
            assert original.read(name) == candidate.read(name) == raw, name
        if strict_xattrs:
            projection = xattr_projection(candidate.index)
            for name, values in tags.items():
                assert projection.get(name, {}).get(KEY.encode()) == values[KEY], name
            for name in expected:
                if name not in tags:
                    assert KEY.encode() not in projection.get(name, {}), name
            with tempfile.TemporaryDirectory(prefix="j24g73-extract-") as td:
                output = Path(td)
                candidate.extractall(output, require_xattrs=True)
                for name, raw in expected.items():
                    assert (output / name).read_bytes() == raw, name
                    got = native_attr(output / name, KEY)
                    want = tags[name][KEY] if name in tags else None
                    assert got == want, ("physical xattr loss", name, got, want)
    pf = preflight_archive(path)
    assert pf["files"] == len(expected) and pf["delta_depth"] == DEPTH
    assert sha256_file(path) == physical
    chain = footer_chain(path)
    assert len(chain) == DEPTH + 1
    assert chain[-1]["kind"] == 0 and all(entry["kind"] == 1 for entry in chain[:-1])
    assert all(entry["op_width"] == 1 for entry in chain[:-1])
    return {
        "archive_sha256": physical, "archive_bytes": path.stat().st_size,
        "index_sha256": fingerprint(expected_index), "members": len(expected),
        "xattr_records": len(xattr_projection(expected_index)), "footers": len(chain),
        "ops": {key: sum(1 for delta in deltas if delta["ops"][0][0] == key)
                for key in ("del", "put", "ren")}, "preflight": pf["files"],
    }


def make_archive(root, family, strict_xattrs):
    src = root / (family + "-tree")
    src.mkdir()
    expected, tags = {}, {}
    n = 2111 if family == "delete" else 128
    tagged = {0, 42, 64, 100} if strict_xattrs and family == "mixed" else set()
    for i in range(n):
        name = f"f{i:04d}.dat"
        raw = hashlib.sha256(f"j24g73-{family}-{i}".encode()).digest() * 2
        path = src / name
        path.write_bytes(raw)
        expected[name] = raw
        if i in tagged:
            value = f"physical-id-{i}".encode()
            _xattrs.setxattr(path, KEY, value, follow_symlinks=False)
            assert native_attr(path, KEY) == value
            tags[name] = {KEY: value}
    archive = root / (family + ".cmpct")
    Builder(src, workers=1, reproducible=False).build(archive)
    if strict_xattrs and family == "mixed":
        with CMPCT(archive) as reader:
            projection = xattr_projection(reader.index)
            for name, record in tags.items():
                assert projection.get(name, {}).get(KEY.encode()) == record[KEY]
    if family == "delete":
        for i in range(DEPTH):
            name = f"f{i:04d}.dat"
            tx.append_delete(archive, name)
            del expected[name]
    else:
        for i in range(21):
            old, new = f"f{i:04d}.dat", f"r{i:04d}.dat"
            tx.append_rename(archive, old, new)
            expected[new] = expected.pop(old)
            if old in tags:
                tags[new] = tags.pop(old)
            removed = f"f{32+i:04d}.dat"
            tx.append_delete(archive, removed)
            del expected[removed]
            tags.pop(removed, None)
            replacement = hashlib.sha256(f"j24g73-updated-{i}".encode()).digest() * 2
            new_source = root / ("put-source-" + str(i))
            new_source.write_bytes(replacement)
            target = (f"f{32+i:04d}.dat" if i == 10 else
                      f"f{64+i:04d}.dat" if i % 2 == 0 else
                      f"new{i:04d}.dat")
            tx.append_update(archive, target, new_source)
            expected[target] = replacement
    assert len(expected) == (2048 if family == "delete" else 118), len(expected)
    return archive, expected, tags


def recovery_test(path):
    data = path.read_bytes()
    results = {}
    for mode, damaged in (("bad-footer-sha", data[:-1] + bytes([data[-1] ^ 0xB5])),
                          ("truncated-footer", data[:-17])):
        with tempfile.TemporaryDirectory(prefix="j24g73-tail-") as td:
            target = Path(td) / (mode + ".cmpct")
            target.write_bytes(damaged)
            with CMPCT(target) as a, FactoredCMPCT(target) as b:
                assert a.index == b.index
                assert a.delta_depth == b.delta_depth
                assert a.latest_footer_pos == b.latest_footer_pos
                assert msgpack.packb(a.index, use_bin_type=True) == msgpack.packb(b.index, use_bin_type=True)
                assert a.delta_depth == DEPTH - 1, (mode, a.delta_depth)
                results[mode] = {"recovered_depth": a.delta_depth,
                                 "index_sha256": fingerprint(a.index)}
    return results


def timed_open(path, candidate):
    cls = FactoredCMPCT if candidate else CMPCT
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    with cls(path) as reader:
        assert reader.delta_depth == DEPTH
        if candidate:
            assert reader._research_route == "factored"
        _ = len(reader.files)
    return {"wall_ns": time.perf_counter_ns() - t0,
            "cpu_ns": time.process_time_ns() - c0}


def benchmark(path):
    for _ in range(4):
        timed_open(path, False)
        timed_open(path, True)
    raw = []
    for block in range(BLOCKS):
        # 2 balanced ABBA orders per block -> 32 measured opens per variant.
        for order in ("ABBA", "BAAB"):
            for letter in order:
                variant = "reference" if letter == "A" else "factored"
                sample = timed_open(path, letter == "B")
                raw.append({"block": block, "order": order, "variant": variant, **sample})
    medians = {}
    for metric in ("wall_ns", "cpu_ns"):
        medians[metric] = {
            variant: statistics.median(row[metric] for row in raw if row["variant"] == variant)
            for variant in ("reference", "factored")}
    tracemalloc_peaks = {}
    for variant in ("reference", "factored"):
        tracemalloc.start()
        tracemalloc.reset_peak()
        timed_open(path, variant == "factored")
        tracemalloc_peaks[variant] = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
    return {"samples": raw, "medians": medians, "tracemalloc_peak_bytes": tracemalloc_peaks,
            "wall_speedup": medians["wall_ns"]["reference"] / medians["wall_ns"]["factored"]}


def rss_probe(path, variant):
    import psutil
    # Fresh process for each variant. Peak is exploratory: imports/allocator
    # baseline can dominate small changes, so RSS is not a release claim.
    cls = FactoredCMPCT if variant == "factored" else CMPCT
    with cls(path) as reader:
        assert reader.delta_depth == DEPTH
        assert reader.index["files"]
    info = psutil.Process().memory_info()
    result = {"rss_bytes": info.rss}
    if hasattr(info, "peak_wset"):
        result["peak_rss_bytes"] = info.peak_wset
    else:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result["peak_rss_bytes"] = int(peak if sys.platform == "darwin" else peak * 1024)
    print(json.dumps(result, sort_keys=True))


def run_rss_probes(path):
    out = {}
    for variant in ("reference", "factored"):
        runs = []
        for _ in range(3):
            p = subprocess.run([sys.executable, __file__, "--rss-probe", str(path), variant],
                               text=True, capture_output=True)
            assert p.returncode == 0, (variant, p.stdout, p.stderr)
            runs.append(json.loads(p.stdout.strip().splitlines()[-1]))
        out[variant] = runs
    return out


def main():
    source = attest()
    outdir = Path(os.environ.get("J24G73_EVIDENCE_DIR", "evidence"))
    outdir.mkdir(parents=True, exist_ok=True)
    strict = sys.platform in ("linux", "darwin")
    if strict:
        assert _xattrs.can_list() and _xattrs.can_set(), "native xattr provider unavailable"
    receipt = {
        "schema": "cmpct-j24g73-research-v1", "source": source,
        "host": platform.platform(), "os": sys.platform,
        "python": platform.python_version(), "strict_posix_xattrs": strict,
        "cases": {}, "product_credit": 0,
        "scope": "research subclass only; physical full Reader-open warm process; no release",
    }
    try:
        with tempfile.TemporaryDirectory(prefix="j24g73-work-") as td:
            root = Path(td)
            for family in ("delete", "mixed"):
                path, expected, tags = make_archive(root, family, strict)
                baseline = verify_pair(path, expected, tags, strict and family == "mixed")
                recovery = recovery_test(path)
                measurements = benchmark(path)
                rss = run_rss_probes(path)
                saved = outdir / (family + "-physical.cmpct")
                shutil.copyfile(path, saved)
                assert sha256_file(saved) == baseline["archive_sha256"]
                receipt["cases"][family] = {
                    "physical": baseline, "recovery": recovery,
                    "benchmark": measurements, "rss_probes": rss,
                }
        deltas = receipt["cases"]["delete"]["benchmark"]
        gain = deltas["wall_speedup"]
        alloc = (deltas["tracemalloc_peak_bytes"]["factored"] -
                 deltas["tracemalloc_peak_bytes"]["reference"])
        receipt["local_mechanism_result"] = {
            "delete_reader_speedup": gain, "traced_peak_delta_bytes": alloc,
            "meets_local_threshold": bool(gain >= 2.0 and alloc <= 2 * 1024 * 1024),
        }
        receipt["status"] = "PASS"
    except BaseException as exc:
        receipt["status"] = "FAIL"
        receipt["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        dest = outdir / "j24g73-result.json"
        dest.write_text(json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n")
        print("J24G73_RECEIPT", dest, "STATUS", receipt.get("status"))
        if receipt.get("local_mechanism_result"):
            print("J24G73_LOCAL_RESULT", json.dumps(receipt["local_mechanism_result"]))
        print("J24G73_HEAD", source["head"])


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--rss-probe":
        rss_probe(Path(sys.argv[2]), sys.argv[3])
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("usage: j24g73_reader_open.py [--rss-probe path reference|factored]")
