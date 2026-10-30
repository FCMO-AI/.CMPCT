#!/usr/bin/env python3
"""J24G74: bounded ownership-transfer replay experiment; never shipping source."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc

import msgpack
from cmpct.reader import CMPCT
from cmpct.journal_replay import JournalReplayAdmissionError
from j24g64_mixed_fsmeta_oracle import admit, factored, reference, fingerprint, make_case
from j24g73_reader_open import (
    FactoredCMPCT, make_archive, verify_pair, recovery_test, sha256_file, ROOT, DEPTH,
)

PREREG = "59c74a86cb87b715da91bd8207c7ce2282256766"
PARENT = "2bd44b03a37360b4c59af3bb6445553b2435ffff"
FIXED_BLOBS = {
    "src/cmpct/reader.py": "29a8be64f3acfb027750351c6a567fd82cf7dc97",
    "research/j24g64_mixed_fsmeta_oracle.py": "7657a41d11f2b3c8136c0b69cfe62401f9b19ccb",
    "research/j24g73_reader_open.py": "9b2fa7c2d625cce84597212673c35fba29dcafd5",
}
CASES = ("delete", "mixed")
LABELS = ("reference", "factored", "owned")
ORDERS = ("ABC", "ACB", "BAC", "BCA", "CAB", "CBA")


def source_attest():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for sha in (PARENT, PREREG):
        subprocess.run(["git", "merge-base", "--is-ancestor", sha, head],
                       cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    for path, sha in FIXED_BLOBS.items():
        current = subprocess.check_output(["git", "rev-parse", "HEAD:" + path],
                                          cwd=ROOT, text=True).strip()
        assert current == sha, (path, current, sha)
    return {"head": head, "parent": PARENT, "prereg": PREREG, "source_blobs": FIXED_BLOBS}


def owned_factored_fresh(base, deltas, *, max_files=None):
    """TRANSFER freshly-decoded, sole-owned objects; never call with retained inputs.

    No deep-copy is appropriate ONLY because _index_from_footer locally owns
    each msgpack.unpackb return and exposes no references before returning.
    Public/shared-helper callers must continue to use the original factored().
    """
    eligible, reason = admit(base, deltas, max_files)
    if not eligible:
        return factored(base, deltas, max_files=max_files)
    state = base
    live = {row[0]: row for row in state["files"]}
    fsmeta = state.get("fsmeta") or {}
    positions = {
        field: {state["files"][entry[0]][0]: entry[1:]
                for entry in fsmeta.get(field, [])}
        for field in ("owner_overrides", "xattrs")
    }
    for delta in deltas:
        state["blobs"].extend(delta.get("blobs", []))
        op = delta["ops"][0]
        kind = op[0]
        if kind == "ren":
            old, new = op[1:]
            if old != new:
                row = live.pop(old)
                row[0] = new
                live[new] = row
                for mapped in positions.values():
                    if old in mapped:
                        mapped[new] = mapped.pop(old)
        elif kind == "del":
            path = op[1]
            del live[path]
            for mapped in positions.values():
                mapped.pop(path, None)
        else:
            row = op[1]
            live[row[0]] = row
    state["files"] = sorted(live.values(), key=lambda row: row[0])
    for field, mapped in positions.items():
        if field in fsmeta:
            fsmeta[field] = [
                [pos, *mapped[row[0]]]
                for pos, row in enumerate(state["files"]) if row[0] in mapped
            ]
    return state, "owned-fresh-decoder"


class OwnedCMPCT(FactoredCMPCT):
    """Research subclass: copy-free replay only within private decoder lifetime."""
    def _index_from_footer(self, footer_pos):
        chain = []
        pos, depth, seen = footer_pos, 0, set()
        while pos and pos not in seen:
            seen.add(pos)
            decoded = self._decode_generation_payload(pos)
            if decoded is None:
                return None
            kind, payload, prev = decoded
            if kind == 0:
                index = msgpack.unpackb(payload, raw=False)
                if chain:
                    try:
                        index, route = owned_factored_fresh(index, list(reversed(chain)))
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


def ownership_differential():
    routes = {}
    for i in range(500):
        raw_base, raw_deltas, limit = make_case(0xC0642026, i)
        serialized = msgpack.packb([raw_base, raw_deltas], use_bin_type=True)
        base_a, deltas_a = msgpack.unpackb(serialized, raw=False)
        base_b, deltas_b = msgpack.unpackb(serialized, raw=False)
        try:
            expected, old_route = factored(base_a, deltas_a, max_files=limit)
            old_error = None
        except Exception as exc:
            expected, old_error = None, (type(exc).__name__, str(exc))
        try:
            got, new_route = owned_factored_fresh(base_b, deltas_b, max_files=limit)
            new_error = None
        except Exception as exc:
            got, new_error = None, (type(exc).__name__, str(exc))
        assert old_error == new_error, ("error-parity", i, old_error, new_error)
        if old_error is None:
            assert got == expected, ("logical-parity", i)
            assert fingerprint(got) == fingerprint(expected), ("wire-parity", i)
            routes[new_route] = routes.get(new_route, 0) + 1
        assert msgpack.packb([base_a, deltas_a], use_bin_type=True) == serialized
    # Explicit counterexample: this helper is not safe with a retained caller.
    prior = {"files": [["a", 1], ["b", 2]], "blobs": []}
    operations = [{"blobs": [], "ops": [["ren", "a", "z"]]}]
    before = copy.deepcopy(prior)
    output, route = owned_factored_fresh(prior, operations)
    assert route == "owned-fresh-decoder"
    assert prior != before and prior is output, "alias hazard must remain visible"
    assert routes.get("owned-fresh-decoder", 0) >= 20, routes
    return {"total": 500, "routes": routes, "retained_caller_alias_hazard": True}


def verify_owned(path, expected, tags, strict_xattrs):
    before = sha256_file(path)
    with CMPCT(path) as a, FactoredCMPCT(path) as b, OwnedCMPCT(path) as c:
        assert b._research_route == "factored"
        assert c._research_route == "owned-fresh-decoder"
        assert a.delta_depth == b.delta_depth == c.delta_depth == DEPTH
        assert a.latest_footer_pos == b.latest_footer_pos == c.latest_footer_pos
        assert a.index == b.index == c.index
        wire = lambda x: msgpack.packb(x, use_bin_type=True)
        assert wire(a.index) == wire(b.index) == wire(c.index)
        assert set(c.by) == set(expected)
        assert a.verify() == b.verify() == c.verify() == len(expected)
        for name, raw in expected.items():
            assert a.read(name) == b.read(name) == c.read(name) == raw
        if strict_xattrs:
            from j24g73_reader_open import xattr_projection, native_attr, KEY
            projection = xattr_projection(c.index)
            for name, attr in tags.items():
                assert projection.get(name, {}).get(KEY) == attr[KEY], name
            with tempfile.TemporaryDirectory(prefix="j24g74-owned-extract-") as d:
                c.extractall(d, require_xattrs=True)
                for name, raw in expected.items():
                    target = Path(d) / name
                    assert target.read_bytes() == raw
                    assert native_attr(target, KEY) == (
                        tags[name][KEY] if name in tags else None)
    for kind, data in (
        ("bad-sha", path.read_bytes()[:-1] + bytes([path.read_bytes()[-1] ^ 0xB5])),
        ("truncated", path.read_bytes()[:-17]),
    ):
        with tempfile.TemporaryDirectory(prefix="j24g74-tail-") as td:
            altered = Path(td) / (kind + ".cmpct")
            altered.write_bytes(data)
            with CMPCT(altered) as a, FactoredCMPCT(altered) as b, OwnedCMPCT(altered) as c:
                assert a.index == b.index == c.index
                assert a.delta_depth == b.delta_depth == c.delta_depth == DEPTH - 1
    assert sha256_file(path) == before


def timed_open(path, label):
    cls = {"reference": CMPCT, "factored": FactoredCMPCT, "owned": OwnedCMPCT}[label]
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    with cls(path) as reader:
        assert reader.delta_depth == DEPTH
        if label != "reference":
            assert reader._research_route == ("factored" if label == "factored" else "owned-fresh-decoder")
        assert reader.files
    return {"wall_ns": time.perf_counter_ns() - t0,
            "cpu_ns": time.process_time_ns() - c0}


def benchmark(path):
    for _ in range(3):
        for label in LABELS:
            timed_open(path, label)
    raw = []
    for block in range(4):
        for order in ORDERS:
            for letter in order:
                label = LABELS["ABC".index(letter)]
                raw.append({"block": block, "order": order, "variant": label,
                            **timed_open(path, label)})
    medians = {metric: {
        label: statistics.median(r[metric] for r in raw if r["variant"] == label)
        for label in LABELS}
        for metric in ("wall_ns", "cpu_ns")}
    tracked = {}
    for label in LABELS:
        values = []
        for _ in range(3):
            tracemalloc.start()
            tracemalloc.reset_peak()
            timed_open(path, label)
            values.append(tracemalloc.get_traced_memory()[1])
            tracemalloc.stop()
        tracked[label] = values
    return {"samples": raw, "medians": medians, "tracemalloc_peak_repeats": tracked,
            "owned_vs_factored_wall_gain": medians["wall_ns"]["factored"] / medians["wall_ns"]["owned"]}


def rss_probe(path, label):
    import psutil
    timed_open(path, label)
    data = psutil.Process().memory_info()
    out = {"rss_after_close_bytes": data.rss}
    if hasattr(data, "peak_wset"):
        out["peak_rss_bytes"] = data.peak_wset
    else:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        out["peak_rss_bytes"] = int(peak if sys.platform == "darwin" else peak * 1024)
    print(json.dumps(out, sort_keys=True))


def run_rss(path):
    samples = {}
    for label in LABELS:
        values = []
        for _ in range(3):
            task = subprocess.run([sys.executable, __file__, "--rss", str(path), label],
                                  text=True, capture_output=True)
            assert task.returncode == 0, (label, task.stdout, task.stderr)
            values.append(json.loads(task.stdout.strip().splitlines()[-1]))
        samples[label] = values
    return samples


def main():
    source = source_attest()
    dest = Path(os.getenv("J24G74_EVIDENCE_DIR", "evidence"))
    dest.mkdir(parents=True, exist_ok=True)
    strict = sys.platform in ("linux", "darwin")
    receipt = {"schema": "cmpct-j24g74-owned-replay-v1", "source": source,
               "host": platform.platform(), "os": sys.platform,
               "strict_posix_xattrs": strict, "product_credit": 0,
               "cases": {}, "status": "RUNNING"}
    try:
        receipt["differential"] = ownership_differential()
        with tempfile.TemporaryDirectory(prefix="j24g74-owned-") as td:
            root = Path(td)
            for family in CASES:
                path, expected, tags = make_archive(root, family, strict)
                physical = verify_pair(path, expected, tags, strict and family == "mixed")
                verify_owned(path, expected, tags, strict and family == "mixed")
                measurements = benchmark(path)
                rss = run_rss(path)
                shutil.copyfile(path, dest / (family + "-physical.cmpct"))
                assert sha256_file(dest / (family + "-physical.cmpct")) == physical["archive_sha256"]
                receipt["cases"][family] = {
                    "physical": physical, "recovery": recovery_test(path),
                    "benchmark": measurements, "rss_probes": rss}
        comparisons = {}
        for family in CASES:
            result = receipt["cases"][family]["benchmark"]
            peaks = {variant: statistics.median(result["tracemalloc_peak_repeats"][variant])
                     for variant in LABELS}
            comparisons[family] = {
                "owned_vs_factored_wall_gain": result["owned_vs_factored_wall_gain"],
                "median_python_peak_bytes": peaks,
                "python_peak_delta_owned_minus_factored": peaks["owned"] - peaks["factored"],
                "archive_bytes_changed_by_reader": 0,
            }
        receipt["comparison"] = comparisons
        receipt["local_threshold_met"] = all(
            comparisons["delete"][k] >= v for k, v in
            {"owned_vs_factored_wall_gain": 1.10}.items()
        ) and comparisons["delete"]["python_peak_delta_owned_minus_factored"] <= 0
        receipt["status"] = "PASS"  # validity pass, separate from economic H1
    except BaseException as exc:
        receipt["status"] = "FAIL"
        receipt["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        path = dest / "j24g74-result.json"
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n")
        print("J24G74_RECEIPT", path, "status", receipt["status"])
        print("J24G74_LOCAL_THRESHOLD", receipt.get("local_threshold_met"))
        print("J24G74_HEAD", source["head"])


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--rss":
        rss_probe(Path(sys.argv[2]), sys.argv[3])
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("usage: j24g74_owned_decoder_court.py [--rss path reference|factored|owned]")
