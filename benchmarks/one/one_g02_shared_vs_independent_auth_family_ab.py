"""ONE-G0.2 shared-vs-independent authenticated temporal-family A/B.

Referee freeze before result-bearing execution
==============================================
Question: after representation discovery has already identified one basis plus eight exact edited
roots, does ONE's shared basis AuthTree + packed q4 Law/Surprise authentication remain a useful
system-level Pareto improvement when compared against the SAME selective-authentication semantics
implemented independently for every version?

Comparator A stores and authenticates nine independent literal roots.  Every root has its own
80-byte AuthTree and a 4 KiB selective read verifies directly against that root.
Candidate B stores one 80-byte basis AuthTree, eight exact Surprise blobs and eight generic
40-byte Law descriptors authenticated by the already-evidenced packed q4 descriptor tree.  A
4 KiB selective read authenticates the descriptor+Surprise and basis range, then applies the
existing generic translation reconstruction helper.

Discovery/search time is excluded from both sides: this is a carrying-cost experiment after the
family relationship is known.  All persisted index/hash bytes, complete logical payload bytes,
proof traffic, and authentication setup/read elapsed are charged.

Frozen V=8 gate on 64 KiB and 256 KiB, three independent families each:
- every read byte-exact and authenticated; deterministic proof corruption must reject candidate B;
- shared persisted bytes must be strictly lower on every family;
- shared authentication-setup median elapsed <=0.80x independent AuthTree setup on every family;
- shared authenticated bytes touched <=1.25x independent on every selective-read row;
- median shared/independent selective-read elapsed <=1.25x, with no row >1.50x.
If size/setup pass but read cost fails, preserve the structural sharing result and record exported
selective-read debt rather than tuning the frozen leaf/tree/corpus thresholds.

This is CPython/hashlib research evidence, not native/product/comparator/release authority.
"""
from __future__ import annotations

import gc
import json
import os
import random
import time
from statistics import median

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import MASTER_SEED, _edited
from benchmarks.one.one_g02_shared_graph_auth_pair import _surprise_blob, _apply_range
from benchmarks.one.one_g02_shared_graph_auth_multiversion import ROOT_SIZES, MUTATIONS, REQUEST_BYTES
from benchmarks.one.one_g02_shared_graph_auth_descriptor_tree import (
    DESC_CONTROL_BYTES, HEADER_BYTES, _desc_control,
)
from benchmarks.one.one_g02_descriptor_auth_quaternary_ab import _build as _build_q
from benchmarks.one.one_g02_descriptor_auth_packed_proof_ab import _packed_proof, _verify_packed
from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range

LEAF = 80
COUNT = 8
FAMILIES_PER_ROOT = 3
REPETITIONS = 11
INNER_READ = 40
INNER_BUILD = 3
MAX_BUILD_RATIO = 0.80
MAX_TOUCH_RATIO = 1.25
MAX_MEDIAN_READ_RATIO = 1.25
MAX_ROW_READ_RATIO = 1.50


def _families():
    master = random.Random(MASTER_SEED ^ 0x51A7EFA1)
    for size in ROOT_SIZES:
        for base_index in range(FAMILIES_PER_ROOT):
            seed = master.getrandbits(64)
            base = random.Random(seed).randbytes(size)
            edited, blobs, diffs = [], [], []
            for m in MUTATIONS[:COUNT]:
                e = _edited(base, random.Random(seed ^ (m << 32) ^ 0xA11CE5EED), m)
                blob, diff = _surprise_blob(base, e)
                edited.append(e); blobs.append(blob); diffs.append(diff)
            yield size, base_index, base, edited, blobs, diffs


def _time(fn, inner: int) -> int:
    t = time.perf_counter_ns()
    for _ in range(inner):
        fn()
    return time.perf_counter_ns() - t


def _measure(a, b, inner: int):
    for _ in range(2): a(); b()
    av, bv = [], []
    enabled = gc.isenabled(); gc.disable()
    try:
        for r in range(REPETITIONS):
            if r & 1:
                bv.append(_time(b, inner)); av.append(_time(a, inner))
            else:
                av.append(_time(a, inner)); bv.append(_time(b, inner))
    finally:
        if enabled: gc.enable()
    return median(av), median(bv)


def run() -> dict[str, object]:
    family_rows, read_rows, failures, corruption_failures = [], [], [], []
    for size, base_index, base, edited, blobs, diffs in _families():
        roots = [base] + edited
        controls = [_desc_control(i, blobs[i]) for i in range(COUNT)]

        def independent_build():
            return [build_auth_tree(x, LEAF) for x in roots]

        def shared_build():
            return build_auth_tree(base, LEAF), _build_q(controls, blobs)

        independent_trees = independent_build()
        basis_tree, qtree = shared_build()
        ib, sb = _measure(independent_build, shared_build, INNER_BUILD)

        independent_persisted = sum(len(x) + t.stored_index_bytes for x, t in zip(roots, independent_trees))
        shared_persisted = (
            len(base) + basis_tree.stored_index_bytes + HEADER_BYTES + DESC_CONTROL_BYTES * COUNT
            + qtree.stored_nonroot_hash_bytes + sum(map(len, blobs))
        )
        family_rows.append({
            "root_bytes": size,
            "base_index": base_index,
            "independent_persisted_bytes": independent_persisted,
            "shared_persisted_bytes": shared_persisted,
            "persisted_ratio": shared_persisted / independent_persisted,
            "independent_build_median_ns": ib,
            "shared_build_median_ns": sb,
            "build_ratio": sb / ib,
        })

        for version in range(COUNT):
            root_index = version + 1
            center = (size - REQUEST_BYTES) // 2
            start = center - center % LEAF + (version * 17) % LEAF
            if start + REQUEST_BYTES > size:
                start -= LEAF
            iproof = prove_range(edited[version], independent_trees[root_index], start, REQUEST_BYTES)
            bproof = prove_range(base, basis_tree, start, REQUEST_BYTES)
            qproof = _packed_proof(qtree, version)

            def independent_read():
                got = verify_range(iproof, independent_trees[root_index].root, start, REQUEST_BYTES)
                if got != edited[version][start:start + REQUEST_BYTES]:
                    raise AssertionError("independent reconstruction")

            def shared_read():
                _verify_packed(version, COUNT, controls[version], blobs[version], qproof, qtree.root)
                got_basis = verify_range(bproof, basis_tree.root, start, REQUEST_BYTES)
                got = _apply_range(got_basis, start, diffs[version])
                if got != edited[version][start:start + REQUEST_BYTES]:
                    raise AssertionError("shared reconstruction")

            try:
                independent_read(); shared_read()
            except Exception as exc:
                failures.append({"root": size, "base": base_index, "version": version, "reason": type(exc).__name__})

            if qproof and qproof[0]:
                bad = list(qproof); x = bytearray(bad[0]); x[0] ^= 1; bad[0] = bytes(x)
                try:
                    _verify_packed(version, COUNT, controls[version], blobs[version], tuple(bad), qtree.root)
                    corruption_failures.append({"root": size, "base": base_index, "version": version})
                except ValueError:
                    pass

            im, sm = _measure(independent_read, shared_read, INNER_READ)
            independent_touch = iproof.touched_data_bytes + iproof.touched_proof_bytes
            shared_touch = (
                bproof.touched_data_bytes + bproof.touched_proof_bytes
                + HEADER_BYTES + DESC_CONTROL_BYTES + len(blobs[version]) + sum(len(x) for x in qproof)
            )
            read_rows.append({
                "root_bytes": size,
                "base_index": base_index,
                "version": version,
                "independent_authenticated_touch_bytes": independent_touch,
                "shared_authenticated_touch_bytes": shared_touch,
                "touch_ratio": shared_touch / independent_touch,
                "independent_read_median_ns": im,
                "shared_read_median_ns": sm,
                "read_ratio": sm / im,
            })

    persisted_ok = all(r["shared_persisted_bytes"] < r["independent_persisted_bytes"] for r in family_rows)
    build_ok = all(r["build_ratio"] <= MAX_BUILD_RATIO for r in family_rows)
    touch_ok = all(r["touch_ratio"] <= MAX_TOUCH_RATIO for r in read_rows)
    ratios = [r["read_ratio"] for r in read_rows]
    read_ok = median(ratios) <= MAX_MEDIAN_READ_RATIO and max(ratios) <= MAX_ROW_READ_RATIO
    passed = not failures and not corruption_failures and persisted_ok and build_ok and touch_ok and read_ok
    return {
        "schema": "cmpct-one-g02-shared-vs-independent-auth-family-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "basis_leaf_bytes": LEAF,
        "version_count": COUNT,
        "request_bytes": REQUEST_BYTES,
        "frozen_gate": {
            "max_build_ratio": MAX_BUILD_RATIO,
            "max_touch_ratio": MAX_TOUCH_RATIO,
            "max_median_read_ratio": MAX_MEDIAN_READ_RATIO,
            "max_row_read_ratio": MAX_ROW_READ_RATIO,
        },
        "failures": failures,
        "corruption_failures": corruption_failures,
        "median_persisted_ratio": median(r["persisted_ratio"] for r in family_rows),
        "max_persisted_ratio": max(r["persisted_ratio"] for r in family_rows),
        "median_build_ratio": median(r["build_ratio"] for r in family_rows),
        "max_build_ratio": max(r["build_ratio"] for r in family_rows),
        "median_touch_ratio": median(r["touch_ratio"] for r in read_rows),
        "max_touch_ratio": max(r["touch_ratio"] for r in read_rows),
        "median_read_ratio": median(ratios),
        "max_read_ratio": max(ratios),
        "decision": "advance_shared_authenticated_family_pareto" if passed else "shared_authenticated_family_debt",
        "claim_boundary": "same-semantics selective-authentication carrying-cost A/B after discovery; CPython/hashlib only; no canonical wire/native/product/comparator/release authority",
        "family_rows": family_rows,
        "read_rows": read_rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
