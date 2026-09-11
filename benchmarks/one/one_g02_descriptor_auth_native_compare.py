"""ONE-G0.2 exact native binary-vs-quaternary descriptor-authentication A/B.

Referee freeze before result-bearing execution
==============================================
The structural quaternary A/B improved persisted descriptor authentication bytes while keeping
the frozen density/access gate green.  The subsequent exact Python/hashlib compute A/B found a
split result at V=8: build was ~4.7% faster, but verification was ~15.9% slower even though q4
used fewer SHA calls and slightly fewer SHA input bytes.  This experiment discriminates whether
that loss belongs to the authentication geometry or to Python proof/object machinery.

The Python harness generates the SAME frozen ONE-G0.2 family inputs used by the compute A/B,
serializes exact 40-byte descriptor controls plus complete Surprise payloads to a private test
framing, and independently computes the expected binary and quaternary descriptor roots using
the existing reference implementations.  A committed C/OpenSSL implementation must match both
roots before any native timing is accepted.

Native timing covers complete descriptor-tree build and verification of all selected descriptor
leaves against prebuilt proof siblings.  It excludes wire parsing and the basis AuthTree: this is
an authentication-geometry microprofile, not product throughput.

Frozen V=8 decision:
- any root mismatch or native verification failure invalidates timing;
- median q4 build and verification ratios must each be <=1.05x binary;
- at least one V=8 median ratio must be <=0.90x to call the q4 geometry materially faster;
- if both are bounded but neither is <=0.90x, retain q4 as structurally superior with neutral
  native compute evidence;
- if either exceeds 1.05x, preserve the structural win but record native execution debt.
No arity, input family, or threshold may change after execution.
"""
from __future__ import annotations

import json
import os
import random
import struct
import subprocess
import tempfile
from pathlib import Path
from statistics import median

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import MASTER_SEED, _edited
from benchmarks.one.one_g02_shared_graph_auth_pair import _surprise_blob
from benchmarks.one.one_g02_shared_graph_auth_multiversion import ROOT_SIZES, MUTATIONS
from benchmarks.one.one_g02_shared_graph_auth_descriptor_tree import _build_desc_tree, _desc_control
from benchmarks.one.one_g02_descriptor_auth_quaternary_ab import _build as _build_quaternary

COUNTS = (4, 8)
FAMILIES_PER_ROOT = 3
REPS = 31
INNER = 700
MAX_SLOWDOWN = 1.05
MATERIAL_SPEEDUP = 0.90
SRC = Path("benchmarks/one/native/one_g02_descriptor_auth_compare_openssl.c")
BIN = Path("/tmp/one_g02_descriptor_auth_compare_openssl")


def _families():
    master = random.Random(MASTER_SEED ^ 0xA071FA11)
    for size in ROOT_SIZES:
        for base_index in range(FAMILIES_PER_ROOT):
            seed = master.getrandbits(64)
            base = random.Random(seed).randbytes(size)
            surprises = []
            for m in MUTATIONS:
                edited = _edited(base, random.Random(seed ^ (m << 32) ^ 0xA11CE5EED), m)
                blob, _ = _surprise_blob(base, edited)
                surprises.append(blob)
            for count in COUNTS:
                blobs = surprises[:count]
                controls = [_desc_control(i, blobs[i]) for i in range(count)]
                yield size, base_index, controls, blobs


def _write_case(path: Path, controls: list[bytes], blobs: list[bytes]) -> None:
    with path.open("wb") as f:
        f.write(struct.pack("<I", len(blobs)))
        for control, blob in zip(controls, blobs, strict=True):
            if len(control) != 40:
                raise AssertionError("descriptor control drift")
            f.write(struct.pack("<I", len(blob)))
            f.write(control)
            f.write(blob)


def run() -> dict[str, object]:
    subprocess.run(
        ["cc", "-O3", "-Wno-deprecated-declarations", str(SRC), "-lcrypto", "-o", str(BIN)],
        check=True,
    )
    rows = []
    root_mismatches = []
    with tempfile.TemporaryDirectory(prefix="one-g02-desc-native-") as td:
        root = Path(td)
        for case_no, (root_size, base_index, controls, blobs) in enumerate(_families()):
            path = root / f"case-{case_no}.bin"
            _write_case(path, controls, blobs)
            binary = _build_desc_tree(controls, blobs)
            quaternary = _build_quaternary(controls, blobs)
            p = subprocess.run(
                [str(BIN), str(path), str(REPS), str(INNER)],
                check=True, text=True, capture_output=True,
            )
            row = json.loads(p.stdout)
            expected_binary = binary.root.hex()
            expected_quaternary = quaternary.root.hex()
            if row["binary_root"] != expected_binary or row["quaternary_root"] != expected_quaternary:
                root_mismatches.append({
                    "root_size": root_size, "base_index": base_index, "version_count": len(blobs),
                    "python_binary": expected_binary, "native_binary": row["binary_root"],
                    "python_quaternary": expected_quaternary, "native_quaternary": row["quaternary_root"],
                })
            rows.append({"root_size": root_size, "base_index": base_index,
                         "surprise_bytes": sum(len(x) for x in blobs), **row})

    summaries = {}
    for count in COUNTS:
        group = [r for r in rows if r["count"] == count]
        summaries[str(count)] = {
            "median_build_ratio": median(r["build_ratio"] for r in group),
            "max_build_ratio": max(r["build_ratio"] for r in group),
            "median_verify_ratio": median(r["verify_ratio"] for r in group),
            "max_verify_ratio": max(r["verify_ratio"] for r in group),
        }

    if root_mismatches:
        decision = "invalid_native_root_mismatch"
    else:
        v8 = summaries["8"]
        bounded = v8["median_build_ratio"] <= MAX_SLOWDOWN and v8["median_verify_ratio"] <= MAX_SLOWDOWN
        material = min(v8["median_build_ratio"], v8["median_verify_ratio"]) <= MATERIAL_SPEEDUP
        if bounded and material:
            decision = "quaternary_native_geometry_advance"
        elif bounded:
            decision = "quaternary_native_geometry_neutral"
        else:
            decision = "quaternary_native_execution_debt"

    return {
        "schema": "cmpct-one-g02-descriptor-auth-native-compare-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "compiler": "cc -O3; OpenSSL libcrypto SHA-256",
        "repetitions": REPS,
        "inner_iterations": INNER,
        "frozen_gate": {"max_v8_median_slowdown_ratio": MAX_SLOWDOWN,
                        "material_speedup_ratio": MATERIAL_SPEEDUP},
        "root_mismatches": root_mismatches,
        "rows": rows,
        "summaries": summaries,
        "decision": decision,
        "claim_boundary": "hosted x86-64 native descriptor-auth geometry microprofile; exact Python roots required; no basis-tree, wire-parse, end-to-end creator or release authority",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
