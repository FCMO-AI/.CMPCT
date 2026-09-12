from __future__ import annotations

"""Office branch-and-bound page-seed referee.

Mission Lock
============
Earlier evidence established two complementary facts on the repaired Office family:
(1) the sparse recursive cold reader is byte-exact but can exceed the fixed 8x physical-read law
because tiny external LZ77 dependencies recursively rebuild whole prior 4 KiB pages; and
(2) materializing external page seeds removes that recursion (0/1800 locality failures in the
historical all-seed referee) but persists seeds for pages that never needed rehabilitation.

Hypothesis
----------
Use the unchanged recursive reader itself as the cheap opportunity gate. Because it decodes full
4 KiB output pages, any <=4 KiB request touches at most one adjacent page pair. Certify every
adjacent full-page superset against the unchanged 32,768 B budget. Persist seed frames only for
pages participating in a pair whose recursive certificate exceeds the budget. Safe pairs use the
recursive reader; unsafe pairs use the existing seed reader. The selector may depend only on this
measured locality debt -- never path, workload identity, hash, extension, or a tuned threshold.

The mechanism is supported only if every pair certificate and the fixed hostile/boundary probe set
is byte-exact and <=32,768 B after dispatch, and the same-input admission artifact plus the already
preregistered sparse-superframe bytes plus selected seed frames remains strictly smaller than the
source-sealed frozen v0.29 artifact.

Disproof
--------
Any byte mismatch, >32,768 B read/certificate, missing selected seed dependency, loss of same-input
density, or movement of page size/8x/codec/admission semantics falsifies the mechanism.

A pass remains diagnostic: grouped sparse/seed metadata is not yet a canonical serialized,
authenticated, recoverable byte-source reader. Real pread/seeks, outer proofs, corruption/recovery,
fresh-process CPU/RSS, native parity and held-out transfer remain explicit debt.
"""

import argparse
import json
import os
from pathlib import Path
import resource
import time
import zlib

from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_page_seed_cold_reader as SEED
from benchmarks import v030_r4_office_sparse_anchor_cold_reader_transfer as TRANSFER
from benchmarks import v030_r4_office_sparse_superframe_economic_referee as SUPER

SCHEMA = "cmpct-v030-r4-office-gated-page-seed-v1"
PAGE = COLD.PAGE
LIMIT = 8 * PAGE


def _combined(reader) -> int:
    return reader.metadata_bytes() + reader.payload_bytes()


def _pair_bounds(page: int, pages: int, output_bytes: int) -> tuple[int, int]:
    return page * PAGE, min(output_bytes, min(pages, page + 2) * PAGE)


def _rss_bytes() -> int:
    # Hosted lane is Linux; ru_maxrss is KiB there.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    t0_cpu = time.process_time()
    t0_wall = time.perf_counter()

    super_evidence = SUPER.run(work, v029_checkout, worker)
    if not super_evidence["hypothesis"]["grouped_sparse_metadata_fits_same_input_margin"]:
        raise RuntimeError("sparse-superframe prerequisite is not economically supported")

    manifest = json.loads((work / "current" / "manifest.json").read_text())
    pool = (work / "current" / "streams.bin").read_bytes()
    hashes = sorted({rec["stream_hash"] for rec in manifest["derived"].values()})

    selected_seed_bytes_total = 0
    all_seed_bytes_total = 0
    selected_seed_pages_total = 0
    available_seed_pages_total = 0
    unsafe_pairs_total = 0
    pairs_total = 0
    fixed_requests = 0
    exact_failures = 0
    locality_failures = 0
    certificate_failures = 0
    max_symbols = 0
    max_calls = 0
    max_depth = 0
    worst_probe = None
    worst_pair = None
    rows = []

    for h in hashes:
        s = manifest["stream_index"][h]
        comp = pool[s["o"] : s["o"] + s["n"]]
        parsed = DEP.parse_tokens(comp)
        raw = zlib.decompress(comp, -15)
        if parsed["output_bytes"] != len(raw):
            raise RuntimeError("DEFLATE parser/output mismatch")

        anchors, blocks, _sparse_stored = COLD._build_metadata(parsed)
        seeds, all_seed_stored, _seed_logical = SEED._build_seeds(parsed, anchors, raw)
        pages = len(anchors)
        all_seed_bytes_total += all_seed_stored
        available_seed_pages = sum(rec is not None for rec in seeds)
        available_seed_pages_total += available_seed_pages

        unsafe_pair_starts: set[int] = set()
        selected_pages: set[int] = set()

        # Referee phase: exact full-page-pair superset certificate using the unchanged cold reader.
        for p in range(pages):
            a, b = _pair_bounds(p, pages, len(raw))
            r = COLD.ColdReader(comp, anchors, blocks, len(raw))
            if r.read(a, b) != raw[a:b]:
                raise RuntimeError("recursive pair certificate became byte-inexact")
            combined = _combined(r)
            pairs_total += 1
            if combined > LIMIT:
                unsafe_pairs_total += 1
                unsafe_pair_starts.add(p)
                selected_pages.add(p)
                if p + 1 < pages:
                    selected_pages.add(p + 1)

        selected_seed_bytes = sum(
            seeds[p]["frame_bytes"] for p in selected_pages if seeds[p] is not None
        )
        selected_seed_pages = sum(1 for p in selected_pages if seeds[p] is not None)
        selected_seed_bytes_total += selected_seed_bytes
        selected_seed_pages_total += selected_seed_pages
        gated_seeds = [rec if i in selected_pages else None for i, rec in enumerate(seeds)]

        # Builder/hostile phase A: every page-pair superset through the selected runtime branch.
        pair_worst = 0
        for p in range(pages):
            a, b = _pair_bounds(p, pages, len(raw))
            seed_mode = p in unsafe_pair_starts
            r = (
                SEED.SeedReader(comp, anchors, blocks, gated_seeds, len(raw))
                if seed_mode
                else COLD.ColdReader(comp, anchors, blocks, len(raw))
            )
            got = r.read(a, b)
            combined = _combined(r)
            if got != raw[a:b]:
                certificate_failures += 1
            if combined > LIMIT:
                certificate_failures += 1
            pair_worst = max(pair_worst, combined)
            max_symbols = max(max_symbols, r.symbols_decoded)
            max_calls = max(max_calls, r.recursive_calls)
            max_depth = max(max_depth, r.max_depth)
            q = {
                "stream_sha256": h,
                "pair_start_page": p,
                "combined_bytes": combined,
                "amplification_vs_4k_contract": combined / PAGE,
                "seed_mode": seed_mode,
            }
            if worst_pair is None or combined > worst_pair["combined_bytes"]:
                worst_pair = q

        # Builder/hostile phase B: inherited fixed aligned/tail/boundary-crossing request surface.
        probe_worst = 0
        stream_requests = 0
        for start in TRANSFER._starts(len(raw)):
            end = min(start + PAGE, len(raw))
            p0 = start // PAGE
            p1 = (end - 1) // PAGE
            if p1 != p0:
                seed_mode = p0 in unsafe_pair_starts
            else:
                seed_mode = p0 in unsafe_pair_starts or (p0 > 0 and (p0 - 1) in unsafe_pair_starts)
            r = (
                SEED.SeedReader(comp, anchors, blocks, gated_seeds, len(raw))
                if seed_mode
                else COLD.ColdReader(comp, anchors, blocks, len(raw))
            )
            got = r.read(start, end)
            combined = _combined(r)
            stream_requests += 1
            fixed_requests += 1
            if got != raw[start:end]:
                exact_failures += 1
            if combined > LIMIT:
                locality_failures += 1
            probe_worst = max(probe_worst, combined)
            max_symbols = max(max_symbols, r.symbols_decoded)
            max_calls = max(max_calls, r.recursive_calls)
            max_depth = max(max_depth, r.max_depth)
            q = {
                "stream_sha256": h,
                "start": start,
                "end": end,
                "combined_bytes": combined,
                "amplification": combined / max(1, end - start),
                "seed_mode": seed_mode,
                "symbols_decoded": r.symbols_decoded,
                "recursive_calls": r.recursive_calls,
                "max_depth": r.max_depth,
            }
            if worst_probe is None or combined > worst_probe["combined_bytes"]:
                worst_probe = q

        rows.append({
            "stream_sha256": h,
            "raw_bytes": len(raw),
            "compressed_bytes": len(comp),
            "pages": pages,
            "page_pairs": pages,
            "unsafe_pairs": len(unsafe_pair_starts),
            "selected_pages": len(selected_pages),
            "available_seed_pages": available_seed_pages,
            "selected_seed_pages": selected_seed_pages,
            "all_seed_stored_bytes": all_seed_stored,
            "selected_seed_stored_bytes": selected_seed_bytes,
            "fixed_requests": stream_requests,
            "worst_pair_bytes_after_dispatch": pair_worst,
            "worst_fixed_probe_bytes": probe_worst,
        })

    current_bytes = int(super_evidence["current_admission"]["stored_bytes"])
    v029_bytes = int(super_evidence["frozen_v029"]["stored_bytes"])
    sparse_grouped = int(super_evidence["superframe"]["stored_sparse_metadata_bytes"])
    candidate = current_bytes + sparse_grouped + selected_seed_bytes_total
    margin = v029_bytes - candidate
    supported = (
        exact_failures == 0
        and locality_failures == 0
        and certificate_failures == 0
        and margin > 0
    )

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "source": super_evidence["source"],
        "frozen_v029": super_evidence["frozen_v029"],
        "current_admission": super_evidence["current_admission"],
        "sparse_superframe": {
            "groups": super_evidence["superframe"]["groups"],
            "stored_sparse_metadata_bytes": sparse_grouped,
            "record_body_bytes": super_evidence["superframe"]["record_body_bytes_unchanged"],
            "largest_group_stored_bytes": super_evidence["superframe"]["largest_group_stored_bytes"],
        },
        "branch_and_bound": {
            "pair_certificates": pairs_total,
            "unsafe_pairs": unsafe_pairs_total,
            "available_seed_pages": available_seed_pages_total,
            "selected_seed_pages": selected_seed_pages_total,
            "all_seed_stored_bytes": all_seed_bytes_total,
            "selected_seed_stored_bytes": selected_seed_bytes_total,
            "seed_storage_fraction": selected_seed_bytes_total / max(1, all_seed_bytes_total),
            "fixed_requests": fixed_requests,
            "exact_failures": exact_failures,
            "locality_failures": locality_failures,
            "certificate_failures": certificate_failures,
            "worst_fixed_probe": worst_probe,
            "worst_page_pair_certificate": worst_pair,
            "max_symbols_decoded": max_symbols,
            "max_recursive_calls": max_calls,
            "max_recursion_depth": max_depth,
            "rows": rows,
        },
        "charged_economics": {
            "candidate_before_locality_metadata_bytes": current_bytes,
            "grouped_sparse_metadata_bytes": sparse_grouped,
            "selected_seed_metadata_bytes": selected_seed_bytes_total,
            "candidate_plus_gated_locality_bytes": candidate,
            "same_input_v029_bytes": v029_bytes,
            "margin_to_same_input_v029_bytes": margin,
        },
        "builder_profile": {
            "cpu_s_including_same_input_referee_and_certification": time.process_time() - t0_cpu,
            "wall_s_including_same_input_referee_and_certification": time.perf_counter() - t0_wall,
            "hosted_process_peak_rss_bytes": _rss_bytes(),
        },
        "hypothesis": {
            "gated_page_seeds_close_locality_within_same_input_economics": supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "fixed_page_bytes": PAGE,
            "fixed_limit_bytes": LIMIT,
            "same_input_source_sealed_v029": True,
            "same_admission_candidate": True,
            "same_sparse_record_information": True,
            "selector_uses_only_measured_locality_debt": True,
            "no_parameter_or_codec_sweep": True,
            "runtime_parent_graph_used": False,
            "runtime_token_list_used": False,
            "runtime_decoded_owner_used": False,
            "remaining_debt": "serialize/authenticate/recover grouped sparse+seed metadata from bytes; actual pread/seeks and outer proofs; hostile corruption/resource bounds; isolate builder certification cost; native/platform parity; held-out transfer",
        },
        "next_if_supported": "productize one serialized authenticated metadata layout for sparse groups + gated seeds, then cold-pread hostile/locality/CPU/RSS and held-out transfer gates",
        "next_if_falsified": "preserve branch-and-bound lower bound; compress/group only selected seed information or redesign restart state without moving 4KiB/8x semantics",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-gated-seed-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-gated-page-seed.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "sparse_superframe": d["sparse_superframe"],
        "branch_and_bound": {k: v for k, v in d["branch_and_bound"].items() if k != "rows"},
        "charged_economics": d["charged_economics"],
        "builder_profile": d["builder_profile"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
