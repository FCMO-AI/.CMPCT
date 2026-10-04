from __future__ import annotations

"""Sparse decoded-dependency lower bound for the Analytics exact-NPZ owner.

The prior contiguous-cone oracle showed that a 4 KiB request can require a 53,340 B contiguous
history span (13.02x), so ordinary restart/window checkpoints cannot satisfy the <=8x locality
contract without changing the ownership model. That does not yet falsify a sparse dependency graph:
a DEFLATE copy byte depends on one earlier decoded byte, and many requested bytes may share ancestors.

This diagnostic parses the exact frozen raw-DEFLATE member, records each decoded byte's immediate
LZ77 parent (-1 for literals/stored bytes), and measures the exact unique transitive decoded-byte
closure for every 4 KiB-aligned request plus the final 4 KiB suffix. It is deliberately an optimistic
lower bound: it does not charge compressed-token fetches, graph metadata, authentication, seeks or
range fragmentation. Therefore a failure is decisive for sparse decoded ownership, while a pass only
authorizes building and charging a physical representation.

Pre-registered disproof: if any measured 4 KiB request needs >32,768 unique decoded bytes including the
request itself, reject a sparse decoded-byte dependency graph as sufficient for the <=8x locality goal.
No threshold sweep and no product-format change are permitted in this oracle.
"""

import argparse
from array import array
import json
import os
from pathlib import Path
import shutil
import time
import zipfile
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE

SCHEMA = "cmpct-v030-r4-deflate-sparse-dependency-oracle-v1"
REQUEST = 4 * 1024
LIMIT_AMP = 8.0
DUAL_OWNER_BYTES = 4_453_188
ACCEPTED_V029_ANALYTICS = DUAL.ACCEPTED_V029_ANALYTICS


def parse_parents(raw_deflate: bytes) -> dict:
    """Return one immediate decoded-byte parent per output byte and exact token statistics."""
    br = CONE.BitReader(raw_deflate)
    parents = array("i")
    token_count = 0
    literal_tokens = 0
    copy_tokens = 0
    blocks = 0
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
                parents.append(-1)
                token_count += 1
                literal_tokens += 1
        elif btype in (1, 2):
            ll, dd = CONE.FIXED if btype == 1 else CONE._dynamic(br)
            while True:
                sym = CONE._decode(br, ll)
                if sym < 256:
                    parents.append(-1)
                    token_count += 1
                    literal_tokens += 1
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
                    if distance > len(parents):
                        raise ValueError("distance beyond output")
                    token_count += 1
                    copy_tokens += 1
                    for _ in range(length):
                        parents.append(len(parents) - distance)
                else:
                    raise ValueError("reserved literal/length symbol")
        else:
            raise ValueError("reserved DEFLATE block type")
        blocks += 1
        if final:
            break
    return {
        "parents": parents,
        "blocks": blocks,
        "tokens": token_count,
        "literal_tokens": literal_tokens,
        "copy_tokens": copy_tokens,
        "consumed_bits": br.bit,
    }


def closure_for_request(parents: array, marks: array, generation: int, start: int, end: int) -> dict:
    """Count exact unique decoded-byte ancestors for [start,end) using generation-stamped marks."""
    stack = list(range(start, end))
    count = 0
    max_depth = 0
    while stack:
        node = stack.pop()
        if marks[node] == generation:
            continue
        marks[node] = generation
        count += 1
        parent = parents[node]
        depth = 0
        while parent >= 0 and marks[parent] != generation:
            marks[parent] = generation
            count += 1
            depth += 1
            parent = parents[parent]
        if depth > max_depth:
            max_depth = depth
    width = end - start
    return {
        "start": start,
        "end": end,
        "request_bytes": width,
        "unique_decoded_closure_bytes": count,
        "amplification": count / max(1, width),
        "max_new_chain_depth": max_depth,
    }


def _request_starts(n: int) -> list[int]:
    if n <= REQUEST:
        return [0]
    starts = list(range(0, n - REQUEST + 1, REQUEST))
    tail = n - REQUEST
    if starts[-1] != tail:
        starts.append(tail)
    return starts


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_r4_sparse_dep_neutral")
    repair = V029._load(V029.REPAIR_PATH, "cmpct_r4_sparse_dep_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"

    relation = DUAL._npz_relation(source)["accepted"]
    npz = source.joinpath(*Path(relation["npz_path"]).parts)
    info, comp, expected, method = CONE._raw_zip_member(npz, relation["member"])
    if method != zipfile.ZIP_DEFLATED:
        raise RuntimeError(f"expected DEFLATE member, got method={method}")

    t0 = time.perf_counter()
    parsed = parse_parents(comp)
    parse_wall = time.perf_counter() - t0
    actual = zlib.decompress(comp, -15)
    if actual != expected or len(parsed["parents"]) != len(actual):
        raise RuntimeError("sparse dependency parser mismatch")

    starts = _request_starts(len(actual))
    marks = array("I", [0]) * len(actual)
    worst = None
    total_closure = 0
    probe_t0 = time.perf_counter()
    for generation, start in enumerate(starts, 1):
        row = closure_for_request(parsed["parents"], marks, generation, start, min(start + REQUEST, len(actual)))
        total_closure += row["unique_decoded_closure_bytes"]
        if worst is None or row["amplification"] > worst["amplification"]:
            worst = row
    probe_wall = time.perf_counter() - probe_t0
    assert worst is not None

    aux_budget = ACCEPTED_V029_ANALYTICS - DUAL_OWNER_BYTES
    pass_floor = worst["amplification"] <= LIMIT_AMP
    # These are illustrative physical-index envelopes, not evidence that such an index is sufficient.
    token_index_8 = parsed["tokens"] * 8
    token_index_12 = parsed["tokens"] * 12
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "04_analytics_and_database",
        "relation": relation,
        "member": {
            "compressed_bytes": len(comp),
            "raw_bytes": len(actual),
            "crc32": info.CRC,
            "compress_type": info.compress_type,
        },
        "parser": {
            "blocks": parsed["blocks"],
            "tokens": parsed["tokens"],
            "literal_tokens": parsed["literal_tokens"],
            "copy_tokens": parsed["copy_tokens"],
            "consumed_bits": parsed["consumed_bits"],
            "stream_bits": len(comp) * 8,
            "parse_wall_s": parse_wall,
            "exact_raw_match": True,
        },
        "sparse_dependency_closure": {
            "request_bytes": REQUEST,
            "limit_amplification": LIMIT_AMP,
            "request_policy": "all 4KiB-aligned windows plus exact final 4KiB suffix",
            "requests": len(starts),
            "worst": worst,
            "mean_unique_decoded_closure_bytes": total_closure / len(starts),
            "probe_wall_s": probe_wall,
            "passes_sparse_decoded_floor": pass_floor,
        },
        "economics": {
            "dual_owner_bytes": DUAL_OWNER_BYTES,
            "accepted_v029_bytes": ACCEPTED_V029_ANALYTICS,
            "max_auxiliary_bytes_to_beat_v029": aux_budget,
            "illustrative_8B_per_token_index_bytes": token_index_8,
            "illustrative_12B_per_token_index_bytes": token_index_12,
            "8B_index_within_budget": token_index_8 <= aux_budget,
            "12B_index_within_budget": token_index_12 <= aux_budget,
        },
        "hypothesis": {
            "sparse_decoded_dependency_graph_can_meet_8x_lower_bound": pass_floor,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "no_product_format_change": True,
            "no_threshold_sweep": True,
            "no_duplicate_decoded_view": True,
            "lower_bound_only": True,
            "aligned_request_scope": True,
            "important_limitation": "closure counts unique decoded byte dependencies only; it gifts compressed-token I/O, graph/index bytes, authentication, seeks, range fragmentation and reader implementation work",
        },
        "next_if_supported": "build a compact authenticated token/range graph prototype and charge exact metadata, physical pread bytes, auth/recovery and reader complexity under the same 1.682 MB Analytics budget",
        "next_if_falsified": "preserve negative and change the owner boundary; even ideal sparse decoded ownership cannot meet <=8x on the measured requests",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-deflate-sparse-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-deflate-sparse.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps({"member": d["member"], "parser": d["parser"], "sparse_dependency_closure": d["sparse_dependency_closure"], "economics": d["economics"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
