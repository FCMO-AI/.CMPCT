from __future__ import annotations

"""Office transfer falsifier for the R4 sparse-anchor cold DEFLATE reader.

Mission lock
============
The resource-tight dependency certificate proved that the eight SFV4 Office derived
streams have <=8x logical dependency closure, while the Analytics cold reader showed
that 4 KiB page anchors + DEFLATE block state can reconstruct without a runtime token
list, parent graph, or decoded owner. This experiment asks whether that *same fixed
mechanism* transfers to Office.

For every unique compressed stream referenced by an SFV4 derived loose-file view we
build exactly the existing cold-reader metadata, then issue every aligned 4 KiB read
plus a fixed boundary-crossing read beginning one byte before each internal 4 KiB
boundary. Each request gets a fresh reader cache. Stored metadata and metadata+payload
bytes touched are charged. Returned bytes must be exact.

Falsify if any read is byte-inexact, any charged selective read exceeds 32,768 bytes,
or SFV4 + all persisted sparse-anchor metadata reaches/exceeds the frozen v0.29 Office
floor. No page-size, anchor-spacing, codec, threshold, request-size, corpus, path, or
hash sweep is allowed. This is still a transfer prototype rather than product locality:
it does not yet deserialize metadata from archive bytes or issue real os.pread calls,
and archive-rooted authentication/recovery, corruption bounds, fresh-process RSS/CPU,
and native parity remain debt.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-sparse-anchor-cold-reader-transfer-v1"
PAGE = 4096
LIMIT = 8 * PAGE


def _starts(n: int) -> list[int]:
    if n <= PAGE:
        return [0]
    starts = set(range(0, n - PAGE + 1, PAGE))
    starts.add(n - PAGE)
    for boundary in range(PAGE, n, PAGE):
        s = boundary - 1
        if s + PAGE <= n:
            starts.add(s)
    return sorted(starts)


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_sparsecold_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_sparsecold_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"

    built = SFV4.build_candidate(source, work / "sfv4", work / "sfv4-work")
    derived = built["derived_inventory"]
    streams = built["all_streams"]
    hashes = sorted({rec["stream_hash"] for rec in derived.values()})
    if not hashes:
        raise RuntimeError("no SFV4 derived streams")

    rows = []
    metadata_total = 0
    request_count = 0
    exact_failures = 0
    locality_failures = 0
    worst = None
    max_depth = 0
    t0 = time.perf_counter()

    for h in hashes:
        comp = streams[h]
        raw = zlib.decompress(comp, -15)
        parsed = DEP.parse_tokens(comp)
        if parsed["output_bytes"] != len(raw):
            raise RuntimeError("DEFLATE parser/output mismatch")
        anchors, blocks, metadata_stored = COLD._build_metadata(parsed)
        metadata_total += metadata_stored
        srow = {
            "stream_sha256": h,
            "compressed_bytes": len(comp),
            "raw_bytes": len(raw),
            "anchors": len(anchors),
            "block_states": len(blocks),
            "metadata_stored_bytes": metadata_stored,
            "requests": 0,
            "exact_failures": 0,
            "locality_failures": 0,
            "worst_combined_bytes": 0,
        }
        for start in _starts(len(raw)):
            end = min(start + PAGE, len(raw))
            reader = COLD.ColdReader(comp, anchors, blocks, len(raw))
            q0 = time.perf_counter()
            got = reader.read(start, end)
            qwall = time.perf_counter() - q0
            exact = got == raw[start:end]
            meta = reader.metadata_bytes()
            payload = reader.payload_bytes()
            combined = meta + payload
            request_count += 1
            srow["requests"] += 1
            if not exact:
                exact_failures += 1
                srow["exact_failures"] += 1
            if combined > LIMIT:
                locality_failures += 1
                srow["locality_failures"] += 1
            srow["worst_combined_bytes"] = max(srow["worst_combined_bytes"], combined)
            max_depth = max(max_depth, reader.max_depth)
            q = {
                "stream_sha256": h,
                "start": start,
                "end": end,
                "request_bytes": end - start,
                "metadata_bytes_touched": meta,
                "payload_bytes_touched": payload,
                "combined_bytes_touched": combined,
                "combined_amplification": combined / max(1, end - start),
                "recursive_calls": reader.recursive_calls,
                "max_recursion_depth": reader.max_depth,
                "symbols_decoded": reader.symbols_decoded,
                "wall_s": qwall,
                "exact": exact,
            }
            if worst is None or q["combined_bytes_touched"] > worst["combined_bytes_touched"]:
                worst = q
        rows.append(srow)

    probe_wall = time.perf_counter() - t0
    sfv4_bytes = int(built["stored_bytes"])
    candidate_with_metadata = sfv4_bytes + metadata_total
    margin = SFV4.ACCEPTED_V029_OFFICE - candidate_with_metadata
    passes = exact_failures == 0 and locality_failures == 0 and margin > 0
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "02_office_workspace",
        "tree_sha256": PRODUCT.treehash(source),
        "streams": rows,
        "summary": {
            "derived_file_count": len(derived),
            "unique_derived_stream_count": len(hashes),
            "requests": request_count,
            "request_bytes": PAGE,
            "limit_bytes": LIMIT,
            "exact_failures": exact_failures,
            "locality_failures": locality_failures,
            "max_recursion_depth": max_depth,
            "worst_combined": worst,
            "probe_wall_s": probe_wall,
        },
        "economics": {
            "sfv4_bytes_before_sparse_metadata": sfv4_bytes,
            "sparse_metadata_stored_bytes": metadata_total,
            "candidate_with_sparse_metadata_bytes": candidate_with_metadata,
            "accepted_v029_office_bytes": SFV4.ACCEPTED_V029_OFFICE,
            "margin_to_v029_bytes": margin,
        },
        "hypothesis": {
            "fixed_sparse_cold_reader_transfers_to_office": passes,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "runtime_parent_graph_used": False,
            "runtime_token_list_used": False,
            "runtime_decoded_owner_used": False,
            "aligned_and_fixed_boundary_crossing_requests": True,
            "no_page_size_sweep": True,
            "no_anchor_spacing_sweep": True,
            "no_codec_sweep": True,
            "no_threshold_sweep": True,
            "no_request_size_sweep": True,
            "remaining_debt": "metadata byte deserialization and actual pread; archive-rooted auth/recovery; corruption and hostile metadata bounds; fresh-process CPU/RSS; native parity",
        },
        "next_if_supported": "serialize/read anchors and block states from authenticated bytes, replace in-memory payload accounting with actual os.pread, then run corruption/resource and fresh-process CPU/RSS gates",
        "next_if_falsified": "preserve the transfer negative and attribute metadata, payload rediscovery, or recursive-work excess before changing representation; do not tune 4KiB/8x",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-sparsecold-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-sparsecold.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"summary": d["summary"], "economics": d["economics"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
