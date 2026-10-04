from __future__ import annotations

"""Streaming structural admission proof for sparse-DEFLATE locality.

Mission Lock / Referee
======================
Held-out receipt 9a21afdf showed that sparse DEFLATE locality is not unconditional: all-zero and
repeated-row NPY streams exceeded the frozen 8x decoded-dependency bound on 930/938 requests, while
ramp and seeded-normal streams passed. The authenticated physical reader at 6b8b625 proved that one
admitted Analytics member can stay below 8x with rooted payload authentication and one-block recovery.

Hypothesis: a workload-independent one-pass structural proof can safely gate the sparse reader without
materializing the full decoded-byte parent graph. For each decoded byte, retain only the earliest
transitive ancestor reachable through LZ77 copy dependencies. For every contiguous 4 KiB output window,
if the span from its minimum earliest ancestor through the window end is <=32 KiB, then the exact sparse
closure is necessarily <=32 KiB because DEFLATE parents always point backward and every ancestor lies
inside that enclosing span. Reject immediately on the first violating window.

Disproof: (1) admit either hostile case already known to exceed the exact 8x closure; (2) reject the
frozen Analytics member that the charged authenticated reader has already demonstrated; (3) disagree
with exact closure in the unsafe direction on any fixed held-out case; or (4) require parent arrays or
full decoded payload materialization. A conservative rejection of an exact-safe held-out case is allowed
but recorded as opportunity loss, not silently retuned.

This is diagnostic admission evidence only. Python parser cost is measured explicitly; a proof that is
semantically safe but too expensive remains engineering debt for native/bulk implementation.
"""

import argparse
from collections import deque
from io import BytesIO
import json
import os
from pathlib import Path
import resource
import shutil
import time
import zipfile
import zlib

import numpy as np

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_sparse_hostile_generalization as HOSTILE
from benchmarks import v030_r4_deflate_sparse_dependency_oracle as EXACT

SCHEMA = "cmpct-v030-r4-deflate-structural-locality-admission-v1"
REQUEST = 4096
LIMIT = 8 * REQUEST
HISTORY = 32768


def _emit_root(roots: list[int], q: deque[tuple[int, int]], pos: int, root: int) -> tuple[bool, int]:
    # Read-copy parent happens before this write, so distance=32768 remains valid in the ring.
    roots[pos % HISTORY] = root
    cutoff = pos - REQUEST
    while q and q[0][0] <= cutoff:
        q.popleft()
    while q and q[-1][1] >= root:
        q.pop()
    q.append((pos, root))
    if pos + 1 < REQUEST:
        return True, pos + 1
    span = (pos + 1) - q[0][1]
    return span <= LIMIT, span


def prove(raw_deflate: bytes) -> dict:
    br = CONE.BitReader(raw_deflate)
    roots = [0] * HISTORY
    q: deque[tuple[int, int]] = deque()
    out_n = 0
    blocks = 0
    tokens = 0
    literals = 0
    copies = 0
    windows_checked = 0
    worst_span = 0
    first_failure = None
    max_queue = 0
    t_wall = time.perf_counter()
    t_cpu = time.process_time()
    rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    def emit_literal() -> bool:
        nonlocal out_n, windows_checked, worst_span, first_failure, max_queue
        ok, span = _emit_root(roots, q, out_n, out_n)
        out_n += 1
        if out_n >= REQUEST:
            windows_checked += 1
            worst_span = max(worst_span, span)
        max_queue = max(max_queue, len(q))
        if not ok and first_failure is None:
            first_failure = {"window_end": out_n, "window_start": out_n - REQUEST, "enclosing_dependency_span_bytes": span}
        return ok

    def emit_copy(distance: int) -> bool:
        nonlocal out_n, windows_checked, worst_span, first_failure, max_queue
        parent = out_n - distance
        if parent < 0:
            raise ValueError("distance beyond output")
        root = roots[parent % HISTORY]
        ok, span = _emit_root(roots, q, out_n, root)
        out_n += 1
        if out_n >= REQUEST:
            windows_checked += 1
            worst_span = max(worst_span, span)
        max_queue = max(max_queue, len(q))
        if not ok and first_failure is None:
            first_failure = {"window_end": out_n, "window_start": out_n - REQUEST, "enclosing_dependency_span_bytes": span}
        return ok

    accepted = True
    while accepted:
        final = br.read(1)
        btype = br.read(2)
        if btype == 0:
            br.align()
            n = br.read(16)
            nn = br.read(16)
            if (n ^ 0xFFFF) != nn:
                raise ValueError("stored block LEN/NLEN mismatch")
            for _ in range(n):
                br.read(8)
                tokens += 1
                literals += 1
                if not emit_literal():
                    accepted = False
                    break
        elif btype in (1, 2):
            ll, dd = CONE.FIXED if btype == 1 else CONE._dynamic(br)
            while accepted:
                sym = CONE._decode(br, ll)
                if sym < 256:
                    tokens += 1
                    literals += 1
                    if not emit_literal():
                        accepted = False
                elif sym == 256:
                    break
                elif 257 <= sym <= 285:
                    li = sym - 257
                    if li >= len(CONE.LEN_BASE):
                        raise ValueError("invalid length symbol")
                    length = CONE.LEN_BASE[li] + br.read(CONE.LEN_EXTRA[li])
                    ds = CONE._decode(br, dd)
                    if ds >= len(CONE.DIST_BASE):
                        raise ValueError("invalid distance symbol")
                    distance = CONE.DIST_BASE[ds] + br.read(CONE.DIST_EXTRA[ds])
                    if distance > out_n:
                        raise ValueError("distance beyond output")
                    tokens += 1
                    copies += 1
                    for _ in range(length):
                        if not emit_copy(distance):
                            accepted = False
                            break
                else:
                    raise ValueError("reserved literal/length symbol")
        else:
            raise ValueError("reserved DEFLATE block type")
        blocks += 1
        if not accepted or final:
            break

    rss1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "accepted": accepted,
        "decoded_bytes_scanned": out_n,
        "windows_checked": windows_checked,
        "worst_enclosing_dependency_span_bytes": worst_span,
        "worst_enclosing_span_amplification": worst_span / REQUEST,
        "first_failure": first_failure,
        "blocks_scanned": blocks,
        "tokens_scanned": tokens,
        "literal_tokens": literals,
        "copy_tokens": copies,
        "consumed_bits": br.bit,
        "wall_s": time.perf_counter() - t_wall,
        "cpu_s": time.process_time() - t_cpu,
        "ru_maxrss_delta_kib": max(0, rss1 - rss0),
        "fixed_root_ring_bytes": HISTORY * 8,
        "max_monotonic_queue_entries": max_queue,
        "full_parent_array_materialized": False,
        "decoded_payload_materialized": False,
    }


def _analytics_member(work: Path) -> tuple[bytes, bytes]:
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_structural_admission_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_structural_admission_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"
    relation = DUAL._npz_relation(source)["accepted"]
    npz = source.joinpath(*Path(relation["npz_path"]).parts)
    _info, comp, expected, method = CONE._raw_zip_member(npz, relation["member"])
    if method != zipfile.ZIP_DEFLATED or zlib.decompress(comp, -15) != expected:
        raise RuntimeError("Analytics member mismatch")
    return comp, expected


def _exact_safe(comp: bytes, raw: bytes) -> dict:
    parsed = EXACT.parse_parents(comp)
    if len(parsed["parents"]) != len(raw):
        raise RuntimeError("exact parser length mismatch")
    starts = EXACT._request_starts(len(raw))
    from array import array
    marks = array("I", [0]) * len(raw)
    worst = 0
    failed = 0
    for generation, start in enumerate(starts, 1):
        row = EXACT.closure_for_request(parsed["parents"], marks, generation, start, min(start + REQUEST, len(raw)))
        worst = max(worst, row["unique_decoded_closure_bytes"])
        failed += row["unique_decoded_closure_bytes"] > LIMIT
    return {"exact_aligned_worst_closure_bytes": worst, "exact_aligned_failed_over_8x": failed, "exact_aligned_safe": failed == 0}


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    comp, raw = _analytics_member(work)
    cases: list[tuple[str, bytes, bytes]] = [("frozen_analytics_member", comp, raw)]
    for name, case_raw in HOSTILE.cases().items():
        case_comp = HOSTILE.raw_deflate(case_raw)
        if zlib.decompress(case_comp, -15) != case_raw:
            raise RuntimeError(f"held-out round trip failed: {name}")
        cases.append((name, case_comp, case_raw))

    rows = []
    unsafe_admissions = 0
    analytics_accepted = False
    conservative_rejections = 0
    for name, c, r in cases:
        exact = _exact_safe(c, r)
        proof = prove(c)
        if proof["accepted"] and not exact["exact_aligned_safe"]:
            unsafe_admissions += 1
        if (not proof["accepted"]) and exact["exact_aligned_safe"]:
            conservative_rejections += 1
        if name == "frozen_analytics_member":
            analytics_accepted = proof["accepted"]
        rows.append({"case": name, "raw_bytes": len(r), "compressed_bytes": len(c), **exact, "structural_proof": proof})

    supported = unsafe_admissions == 0 and analytics_accepted
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "request_bytes": REQUEST,
        "limit_bytes": LIMIT,
        "history_ring_bytes": HISTORY,
        "cases": rows,
        "summary": {
            "unsafe_admissions": unsafe_admissions,
            "conservative_rejections": conservative_rejections,
            "frozen_analytics_accepted": analytics_accepted,
        },
        "hypothesis": {"streaming_structural_proof_is_safe_and_preserves_analytics_opportunity": supported},
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "no_threshold_sweep": True,
            "no_workload_path_hash_dispatch": True,
            "proof_is_sufficient_not_necessary": True,
            "every_4k_window_checked_until_rejection": True,
            "full_parent_array_for_admission": False,
            "decoded_payload_for_admission": False,
            "exact_parent_graph_used_only_as_referee": True,
            "python_proof_cost_is_engineering_debt_not_gifted": True,
        },
        "next_if_supported": "place this proof ahead of sparse-owner admission, preserve exact fallback for rejects, then measure end-to-end selector CPU/RSS and held-out false-negative opportunity before canonical integration",
        "next_if_falsified": "preserve the negative; do not weaken 8x. Replace the sufficient span certificate with a tighter streaming certificate or choose a different owner boundary",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-structural-admission-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-structural-admission.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"summary": d["summary"], "cases": d["cases"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
