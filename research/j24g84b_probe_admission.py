#!/usr/bin/env python3
"""J24G84b: charged Zstd-1 name-frontcode admission scout; science only."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

import msgpack
import zstandard as zstd
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from j24g84_frontcode_whole_index import (ROOT, N, attest, make_archive,
                                          encode_index, decode_index, hostile_roundtrips)

PREREG = "311a6cabbe0e06afd0cab0179f561e750c3ce6dc"
ORIGINAL_SOURCE_BLOB = "71cf5ef26992833f56b2528a891860e25530547e"
LABELS = ("flat", "deep", "random", "unicode", "random_salt", "deep_hash")
OUT = Path(os.getenv("J24G84B_EVIDENCE_DIR", "evidence"))


def make_heldout(root, kind):
    src = root / ("source-" + kind)
    src.mkdir()
    payload = hashlib.sha256(("j24g84b-data-" + kind).encode()).digest()
    for i in range(N):
        h = hashlib.sha256(f"independent-heldout-j24g84b-{kind}-{i}".encode()).hexdigest()
        if kind == "random_salt":
            name = h[:48] + ".bin"
        elif kind == "deep_hash":
            name = f"group-{i//128:03d}/tier-{(i//16)%8:02d}/node-{h[:32]}.dat"
        else:
            raise ValueError(kind)
        dst = src / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(payload)
    dest = root / (kind + ".cmpct")
    start = time.perf_counter_ns()
    Builder(src, workers=1, reproducible=True).build(dest)
    build_ns = time.perf_counter_ns() - start
    with CMPCT(dest) as reader:
        assert len(reader.by) >= N
        assert reader.verify() >= N
        idx = copy.deepcopy(reader.index)
    return idx, dest.stat().st_size, build_ns


def bench_one(index, z1, z19, variant):
    start, cpu = time.perf_counter_ns(), time.process_time_ns()
    baseline = msgpack.packb(index, use_bin_type=True)
    if variant == "control":
        wire = z19.compress(baseline)
        selected = "control"
    elif variant == "probe":
        candidate, _ = encode_index(index)
        a = z1.compress(baseline)
        b = z1.compress(candidate)
        selected = "candidate" if len(b) < len(a) else "control"
        wire = z19.compress(candidate if selected == "candidate" else baseline)
    else:
        raise ValueError(variant)
    wall = time.perf_counter_ns() - start
    cpu_ns = time.process_time_ns() - cpu
    return dict(variant=variant, selected=selected, bytes=len(wire) +
                (1 if selected == "candidate" else 0),
                wall_ns=wall, cpu_ns=cpu_ns)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "merge-base", "--is-ancestor", PREREG, "HEAD"],
                   cwd=ROOT, check=True)
    actual = subprocess.check_output(
        ["git", "rev-parse", "HEAD:research/j24g84_frontcode_whole_index.py"],
        cwd=ROOT, text=True).strip()
    assert actual == ORIGINAL_SOURCE_BLOB, ("old-instrument-drift", actual)
    receipt = dict(schema="j24g84b-charged-admission-o0-v1", source=attest(),
                   host=platform.platform(), prereg=PREREG,
                   status="RUNNING", product_credit=0, cases={})
    dest = OUT / "j24g84b-result.json"
    def save():
        dest.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    save()
    try:
        receipt["hostiles"] = hostile_roundtrips()
        z1 = zstd.ZstdCompressor(level=1, threads=0)
        z19 = zstd.ZstdCompressor(level=19, threads=0)
        with tempfile.TemporaryDirectory(prefix="cmpct-j24g84b-") as td:
            root = Path(td)
            for name in LABELS:
                if name in LABELS[:4]:
                    idx, archive_bytes, build_ns, _ = make_archive(root, name)
                else:
                    idx, archive_bytes, build_ns = make_heldout(root, name)
                original = msgpack.packb(idx, use_bin_type=True)
                candidate, _ = encode_index(idx)
                assert decode_index(candidate) == original
                b19 = z19.compress(original)
                c19 = z19.compress(candidate)
                b1 = z1.compress(original)
                c1 = z1.compress(candidate)
                policy_choice = "candidate" if len(c1) < len(b1) else "control"
                policy_bytes = len(c19) + 1 if policy_choice == "candidate" else len(b19)
                oracle_bytes = min(len(b19), len(c19) + 1)
                order = ("control", "probe", "probe", "control") * 5
                trials = [bench_one(idx, z1, z19, variant) for variant in order]
                assert all(r["selected"] == policy_choice for r in trials if r["variant"] == "probe")
                assert all(r["bytes"] == len(b19) for r in trials if r["variant"] == "control")
                assert all(r["bytes"] == policy_bytes for r in trials if r["variant"] == "probe")
                ctrl = statistics.median(r["wall_ns"] for r in trials if r["variant"] == "control")
                pol = statistics.median(r["wall_ns"] for r in trials if r["variant"] == "probe")
                row = dict(status="COMPLETE", original_index_sha256=hashlib.sha256(original).hexdigest(),
                           recovered_index_sha256=hashlib.sha256(decode_index(candidate)).hexdigest(),
                           archive_bytes=archive_bytes, real_index_rows=len(idx["files"]),
                           builder_wall_ns=build_ns, zstd1_control_bytes=len(b1),
                           zstd1_candidate_bytes=len(c1), zstd19_control_bytes=len(b19),
                           zstd19_candidate_bytes=len(c19), selected=policy_choice,
                           selected_stored_bytes=policy_bytes, gifted_oracle_bytes=oracle_bytes,
                           selector_regret_bytes=policy_bytes-oracle_bytes,
                           saved_bytes=len(b19)-policy_bytes,
                           saved_pct=100*(len(b19)-policy_bytes)/len(b19),
                           h1_positive=(len(b19)-policy_bytes>=256 and
                                        len(b19)-policy_bytes>=.05*len(b19)),
                           h1_false_admission=policy_bytes>len(b19),
                           median_control_wall_ns=ctrl, median_policy_wall_ns=pol,
                           policy_over_control_wall=pol/ctrl, trials=trials)
                receipt["cases"][name] = row
                save()
                print("J24G84b", name, "L1choice", policy_choice,
                      "orig19", len(b19), "policy", policy_bytes,
                      "oracle", oracle_bytes, "wall_ratio", round(pol/ctrl,3),
                      flush=True)
        rows = list(receipt["cases"].values())
        receipt["status"] = "COMPLETE"
        receipt["positive_families"] = sum(r["h1_positive"] for r in rows)
        receipt["false_admissions"] = sum(r["h1_false_admission"] for r in rows)
        receipt["cpu_debt_families"] = sum(r["policy_over_control_wall"] > 1.15 for r in rows)
        receipt["decision"] = ("CHARGED_L1_SCOUT_PROMISING_O0" if
                              receipt["positive_families"] >= 2 and
                              receipt["false_admissions"] == 0 and
                              receipt["cpu_debt_families"] == 0 else
                              "CHARGED_L1_SCOUT_NOT_PRODUCT_ELIGIBLE")
        save()
    except BaseException as exc:
        receipt["status"] = "FAILED"
        receipt["error"] = repr(exc)
        save()
        raise
    print("J24G84b final", receipt["decision"], flush=True)


if __name__ == "__main__":
    main()
