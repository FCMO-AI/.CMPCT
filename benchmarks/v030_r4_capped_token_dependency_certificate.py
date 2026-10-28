from __future__ import annotations

"""Bounded token-level locality certificate for the v0.30 R4 sparse-DEFLATE line.

Mission Lock / Referee
======================
The exhaustive page-pair referee proves decoded dependency work with one parent integer per decoded
byte. That is useful as an oracle but is not acceptable shipping admission state. This experiment asks
whether the same frozen <=8x decision can be reproduced from DEFLATE token ranges plus a per-request
visited set capped at LIMIT+1.

Falsifiable hypothesis: for all eight exact Office SFV4 derived streams and the four hostile controls,
the capped token certificate agrees with the exact byte-parent oracle on every aligned 8 KiB page-pair
superwindow. It must accept all Office streams plus ramp/seeded-normal, reject all-zero/repeated-row,
never retain a decoded-byte parent graph in the candidate certificate, and cap live query state at
32,769 visited byte positions. Any decision mismatch, unsafe acceptance, Office rejection, parser
identity failure, or inventory drift falsifies the mechanism. The 8x threshold is frozen.

This remains diagnostic research. It does not gift product admission: compressed-token physical I/O,
serialized/authenticated metadata, recovery, seeks, reader integration, and real packed-index bytes
must still be charged before product credit.
"""

import argparse
from bisect import bisect_right
import json
import os
from pathlib import Path
import shutil
import time
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_sparse_dependency_oracle as EXACT
from benchmarks import v030_r4_deflate_sparse_hostile_generalization as HOSTILE
from benchmarks import v030_r4_office_exact_stream_federation_v2 as SFV2
from benchmarks import v030_r4_office_sfv3_derived_views as SFV3
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4

SCHEMA = "cmpct-v030-r4-capped-token-dependency-certificate-v1"
PAGE = 4096
LIMIT = 8 * PAGE
CAP = LIMIT + 1
EST_PACKED_TOKEN_BYTES = 12  # conservative research envelope: output start/end + distance as u32


def parse_token_ranges(raw_deflate: bytes) -> dict:
    """Parse raw DEFLATE into output ranges; no per-decoded-byte dependency array is retained."""
    br = CONE.BitReader(raw_deflate)
    starts: list[int] = []
    ends: list[int] = []
    distances: list[int] = []  # 0 => literal/stored range; otherwise parent(p)=p-distance
    out = 0
    blocks = 0
    literal_bytes = 0
    copy_bytes = 0

    def add(length: int, distance: int) -> None:
        nonlocal out, literal_bytes, copy_bytes
        if length <= 0:
            return
        if distance == 0 and distances and distances[-1] == 0 and ends[-1] == out:
            ends[-1] += length
        else:
            starts.append(out)
            ends.append(out + length)
            distances.append(distance)
        if distance:
            copy_bytes += length
        else:
            literal_bytes += length
        out += length

    while True:
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
            add(n, 0)
        elif btype in (1, 2):
            ll, dd = CONE.FIXED if btype == 1 else CONE._dynamic(br)
            while True:
                sym = CONE._decode(br, ll)
                if sym < 256:
                    add(1, 0)
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
                    if distance > out:
                        raise ValueError("distance beyond output")
                    add(length, distance)
                else:
                    raise ValueError("reserved literal/length symbol")
        else:
            raise ValueError("reserved DEFLATE block type")
        blocks += 1
        if final:
            break

    if not starts or starts[0] != 0 or ends[-1] != out:
        raise RuntimeError("token coverage mismatch")
    for i in range(1, len(starts)):
        if starts[i] != ends[i - 1]:
            raise RuntimeError("token gap/overlap")
    return {
        "starts": starts,
        "ends": ends,
        "distances": distances,
        "output_bytes": out,
        "blocks": blocks,
        "token_ranges": len(starts),
        "literal_bytes": literal_bytes,
        "copy_bytes": copy_bytes,
        "consumed_bits": br.bit,
    }


def capped_closure(tokens: dict, start: int, end: int) -> tuple[int, bool, int]:
    """Return (count, exceeded, peak_live_positions) using only token ranges + capped query state."""
    starts = tokens["starts"]
    ends = tokens["ends"]
    distances = tokens["distances"]
    seen: set[int] = set()
    stack = list(range(start, end))
    peak = len(stack)
    while stack:
        p = stack.pop()
        if p in seen:
            continue
        seen.add(p)
        if len(seen) >= CAP:
            return len(seen), True, max(peak, len(seen) + len(stack))
        i = bisect_right(starts, p) - 1
        if i < 0 or p >= ends[i]:
            raise RuntimeError(f"token lookup failed at output byte {p}")
        distance = distances[i]
        if distance:
            parent = p - distance
            if parent < 0:
                raise RuntimeError("negative DEFLATE parent")
            if parent not in seen:
                stack.append(parent)
        peak = max(peak, len(seen) + len(stack))
    return len(seen), False, peak


def pair_starts(n: int) -> list[int]:
    return list(range(0, max(1, n), PAGE))


def compare_stream(name: str, comp: bytes, raw: bytes, expected_unsafe: bool) -> dict:
    if zlib.decompress(comp, -15) != raw:
        raise RuntimeError(f"round-trip failed: {name}")

    t0 = time.perf_counter()
    tokens = parse_token_ranges(comp)
    token_parse_wall = time.perf_counter() - t0
    if tokens["output_bytes"] != len(raw):
        raise RuntimeError(f"token parser length mismatch: {name}")

    # Exact per-byte graph is oracle-only and never supplied to the candidate certificate.
    t0 = time.perf_counter()
    exact = EXACT.parse_parents(comp)
    exact_parse_wall = time.perf_counter() - t0
    if len(exact["parents"]) != len(raw):
        raise RuntimeError(f"exact parser length mismatch: {name}")
    marks = __import__("array").array("I", [0]) * len(raw)

    decision_mismatches = 0
    exact_count_mismatches_below_limit = 0
    candidate_pairs_over = 0
    exact_pairs_over = 0
    worst_candidate_count = 0
    worst_exact_count = 0
    peak_live = 0
    starts = pair_starts(len(raw))
    t0 = time.perf_counter()
    for generation, start in enumerate(starts, 1):
        end = min(start + 2 * PAGE, len(raw))
        c_count, c_over, live = capped_closure(tokens, start, end)
        e = EXACT.closure_for_request(exact["parents"], marks, generation, start, end)
        e_count = e["unique_decoded_closure_bytes"]
        e_over = e_count > LIMIT
        decision_mismatches += c_over != e_over
        if not e_over and c_count != e_count:
            exact_count_mismatches_below_limit += 1
        candidate_pairs_over += c_over
        exact_pairs_over += e_over
        worst_candidate_count = max(worst_candidate_count, c_count)
        worst_exact_count = max(worst_exact_count, e_count)
        peak_live = max(peak_live, live)
    probe_wall = time.perf_counter() - t0

    passes = candidate_pairs_over == 0
    expected_pass = not expected_unsafe
    return {
        "case": name,
        "raw_bytes": len(raw),
        "compressed_bytes": len(comp),
        "expected_exact_unsafe": expected_unsafe,
        "expected_pass": expected_pass,
        "candidate_pass": passes,
        "pairs_checked": len(starts),
        "candidate_pairs_over_8x": candidate_pairs_over,
        "exact_pairs_over_8x": exact_pairs_over,
        "decision_mismatches_vs_exact": decision_mismatches,
        "exact_count_mismatches_below_limit": exact_count_mismatches_below_limit,
        "worst_candidate_closure_bytes": worst_candidate_count,
        "worst_exact_closure_bytes": worst_exact_count,
        "peak_live_query_positions": peak_live,
        "token_parse_wall_s": token_parse_wall,
        "exact_oracle_parse_wall_s": exact_parse_wall,
        "probe_wall_s_including_exact_oracle": probe_wall,
        "token_metadata": {
            "blocks": tokens["blocks"],
            "token_ranges": tokens["token_ranges"],
            "literal_bytes": tokens["literal_bytes"],
            "copy_bytes": tokens["copy_bytes"],
            "estimated_packed_bytes_at_12B_per_range": tokens["token_ranges"] * EST_PACKED_TOKEN_BYTES,
        },
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_capped_token_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_capped_token_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    containers, _shared = SFV2.discover(source)
    all_streams = SFV4._all_member_streams(containers)
    derived = SFV3._derived_inventory(source, containers, all_streams)
    if len(derived) != 8:
        raise RuntimeError(f"Office derived inventory drift: expected 8, got {len(derived)}")

    office = []
    for rel, rec in sorted(derived.items()):
        office.append(compare_stream(f"office:{rel}", all_streams[rec["stream_hash"]], (source / rel).read_bytes(), False))

    hostile_cases = HOSTILE.cases()
    hostile_expectations = {
        "all_zero_f32": True,
        "repeated_row_f32": True,
        "ramp_f32": False,
        "seeded_normal_f32": False,
    }
    if set(hostile_cases) != set(hostile_expectations):
        raise RuntimeError(f"hostile control inventory drift: {sorted(hostile_cases)}")
    controls = [
        compare_stream(name, HOSTILE.raw_deflate(raw), raw, hostile_expectations[name])
        for name, raw in hostile_cases.items()
    ]

    rows = office + controls
    mismatch = sum(r["decision_mismatches_vs_exact"] for r in rows)
    count_mismatch = sum(r["exact_count_mismatches_below_limit"] for r in rows)
    wrong_expected = sum(r["candidate_pass"] != r["expected_pass"] for r in rows)
    max_live = max(r["peak_live_query_positions"] for r in rows)
    supported = mismatch == 0 and count_mismatch == 0 and wrong_expected == 0 and max_live <= CAP
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "page_bytes": PAGE,
        "frozen_decoded_work_limit_bytes": LIMIT,
        "query_state_cap_positions": CAP,
        "office": office,
        "controls": controls,
        "summary": {
            "streams_checked": len(rows),
            "office_streams": len(office),
            "decision_mismatches_vs_exact": mismatch,
            "exact_count_mismatches_below_limit": count_mismatch,
            "wrong_expected_classifications": wrong_expected,
            "max_live_query_positions": max_live,
            "office_max_token_ranges": max(r["token_metadata"]["token_ranges"] for r in office),
            "office_max_estimated_packed_token_bytes": max(r["token_metadata"]["estimated_packed_bytes_at_12B_per_range"] for r in office),
            "office_worst_exact_closure_bytes": max(r["worst_exact_closure_bytes"] for r in office),
        },
        "hypothesis": {"bounded_token_certificate_matches_exact_referee": supported},
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "frozen_8x_limit": True,
            "threshold_sweep": False,
            "candidate_retains_per_decoded_byte_parent_graph": False,
            "exact_parent_graph_used_only_as_referee": True,
            "query_state_capped_at_limit_plus_one": True,
            "physical_io_gifted": True,
            "serialized_authenticated_metadata_gifted": True,
            "auth_recovery_gifted": True,
            "product_admission_authorized": False,
        },
        "next_if_supported": "serialize a compact authenticated token/range index and implement a physical selective reader; charge stored bytes, pread bytes/ranges, auth/recovery, CPU/wall/RSS and reconstruction work before selector integration",
        "next_if_falsified": "preserve mismatch and refine the certificate representation; do not weaken the frozen 8x contract",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-capped-token-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-capped-token.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"summary": d["summary"], "hypothesis": d["hypothesis"], "controls": d["controls"]}, indent=2))


if __name__ == "__main__":
    main()
