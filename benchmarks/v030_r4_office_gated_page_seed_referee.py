from __future__ import annotations

"""Office branch-and-bound page-seed referee.

Mission Lock / Referee
======================
Two earlier results isolate complementary facts on the same repaired Office family:

* the sparse cold reader is byte-exact but can exceed the fixed 8x physical-access law because
  small external LZ77 dependencies recursively reconstruct whole prior pages;
* materializing an external seed for every page kills that recursion (0/1800 locality failures,
  ~2.162x worst observed), but stores seeds for many pages that never needed rehabilitation.

The same-input admission candidate now has only a small density margin over frozen source-sealed
v0.29. The sparse-superframe referee separately tests whether repeated proof traffic, rather than
index information, can be amortized without changing the sparse records.

Hypothesis
----------
Use the unchanged recursive cold reader as a cheap opportunity gate. Because this reader always
decodes complete 4 KiB output pages, every arbitrary <=4 KiB request touches either one page or two
adjacent pages. Certify every adjacent full-page superset against the unchanged 32,768 B budget.
Persist page-seed frames only for pages participating in a pair whose recursive certificate exceeds
that budget. At runtime, requests whose touched page/pair is certified safe use the recursive reader;
requests in an unsafe pair use the seed reader. No workload identity or tuned threshold participates.

The mechanism is supported only if all fixed 4 KiB hostile/boundary probes remain byte-exact and <=8x,
all adjacent-page supersets are <=32,768 B after dispatch, and the same-input admission artifact plus
the *already preregistered* sparse-superframe bytes plus selected seed frames remains strictly smaller
than source-sealed frozen v0.29.

Disproof
--------
Any byte mismatch, >32,768 B probe/certificate, missing selected seed dependency, loss of same-input
density, or movement of page size/8x/codec/admission semantics falsifies the mechanism. The selector
may only branch on the measured locality debt of the same reader operation.

A pass remains diagnostic. Seed frames are still represented as research records and sparse metadata
superframes are not yet a canonical authenticated/recoverable serializer. Actual pread/seeks, outer
root/proofs, corruption/recovery, fresh-process CPU/RSS, native parity and held-out transfer remain debt.
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
    start = page * PAGE
    end = min(output_bytes, min(pages, page + 2) * PAGE)
    return start, end


def _rss_bytes() -> int:
    # Linux ru_maxrss is KiB; this hosted lane is Linux-only and records the unit explicitly.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    t0_cpu = time.process_time()
    t0_wall = time.perf_counter()
    super_evidence = SUPER.run(work, v029_checkout, worker)
    if not super_evidence["hypothesis"]["grouped_sparse_metadata_fits_same_input_margin"]:
        raise RuntimeError("prerequisite sparse-superframe economics are not supported")

    manifest = json.loads((work / "current" / "manifest.json").read_text())
    pool = (work / "current" / "streams.bin").read_bytes()
    hashes = sorted({rec["stream_hash"] for rec in manifest["derived"].values()})

    total_selected_seed_bytes = 0
    total_selected_seed_pages = 0
    total_available_seed_pages = 0
    total_unsafe_pairs = 0
    total_pairs = 0
    fixed_requests = 0
    exact_failures = 0
    locality_failures = 0
    certificate_failures = 0
    max_symbols = 0
    max_recursive_calls = 0
    max_depth = 0
    worst_probe = None
    worst_certificate = None
    rows = []

    for h in hashes:
        s = manifest["stream_index"][h]
        comp = pool[s["o"] : s["o"] + s["n"]]
        parsed = DEP.parse_tokens(comp)
        raw = zlib.decompress(comp, -15)
        if parsed["output_bytes"] != len(raw):
            raise RuntimeError("DEFLATE parser/output mismatch")
        anchors, blocks, _sparse_individual = COLD._build_metadata(parsed)
        seeds, _all_seed_stored, _logical_seed = SEED._build_seeds(parsed, anchors, raw)
        pages = len(anchors)

        unsafe_pair_starts: set[int] = set()
        selected_pages: set[int] = set()
        pair_rows = []
        for p in range(pages):
            a, b = _pair_bounds(p, pages, len(raw))
            r = COLD.ColdReader(comp, anchors, blocks, len(raw))
            got = r.read(a, b)
            if got != raw[a:b]:
                raise RuntimeError("recursive page-pair certificate became byte-inexact")
            combined = _combined(r)
            unsafe = combined > LIMIT
            if unsafe:
                unsafe_pair_starts.add(p)
                selected_pages.add(p)
                if p + 1 < pages:
                    selected_pages.add(p + 1)
            total_pairs += 1
            if unsafe:
                total_unsafe_pairs += 1
            pair_rows.append({
                "page": p,
                "recursive_bytes": combined,
                "recursive_amplification_vs_4k_law": combined / PAGE,
                "unsafe": unsafe,
            })

        # Persist only external seed records for pages that can participate in an unsafe pair.
        selected_seed_bytes = sum(
            seeds[p]["frame_bytes"] for p in selected_pages if seeds[p] is not None
        )
        selected_seed_pages = sum(1 for p in selected_pages if seeds[p] is not None)
        available_seed_pages = sum(1 for rec in seeds if rec is not None)
        total_selected_seed_bytes += selected_seed_bytes
        total_selected_seed_pages += selected_seed_pages
        total_available_seed_pages += available_seed_pages

        gated_seeds = [rec if i in selected_pages else None for i, rec in enumerate(seeds)]

        # Re-run every page-pair superset through the actual branch selected by the certificate.
        cert_worst = 0
        for p in range(pages):
            a, b = _pair_bounds(p, pages, len(raw))
            if p in unsafe_pair_starts:
                r = SEED.SeedReader(comp, anchors, blocks, gated_seeds, len(raw))
            else:
                r = COLD.ColdReader(comp, anchors, blocks, len(raw))
            got = r.read(a, b)
            if got != raw[a:b]:
                certificate_failures += 1
            combined = _combined(r)
            cert_worst = max(cert_worst, combined)
            if combined > LIMIT:
                certificate_failures += 1
            max_symbols = max(max_symbols, r.symbols_decoded)
            max_recursive_calls = max(max_recursive_calls, r.recursive_calls)
            max_depth = max(max_depth, r.max_depth)
            q = {"stream_sha256": h, "pair_start_page": p, "combined_bytes": combined,
                 "seed_mode": p in unsafe_pair_starts, "returned_superset_bytes": b-a}
            if worst_certificate is None or combined > worst_certificate["combined_bytes"]:
                worst_certificate = q

        # Fixed hostile/boundary probes remain a regression surface; dispatch depends only on touched pages.
        probe_worst = 0
        for start in TRANSFER._starts(len(raw)):
            end = min(start + PAGE, len(raw))
            p0 = start // PAGE
            p1 = (end - 1) // PAGE
            # A two-page request uses the corresponding adjacent pair certificate; a one-page request
            # uses seed mode if either adjacent pair containing it is unsafe, which is conservative.
            seed_mode = p0 in unsafe_pair_starts or (p0 > 0 and (p0 - 1) in unsafe_pair_starts)
            if p1 != p0:
                seed_mode = p0 in unsafe_pair_starts
            if seed_mode:
                r = SEED.SeedReader(comp, anchors, blocks, gated_seeds, len(raw))
            else:
                r = COLD.ColdReader(comp, anchors, blocks, len(raw))
            got = r.read(start, end)
            combined = _combined(r)
            fixed_requests += 1
            if got != raw[start:end]:
                exact_failures += 1
            if combined > LIMIT:
                locality_failures += 1
            probe_worst = max(probe_worst, combined)
            max_symbols = max(max_symbols, r.symbols_decoded)
            max_recursive_calls = max(max_recursive_calls, r.recursive_calls)
            max_depth = max(max_depth, r.max_depth)
            q = {"stream_sha256": h, "start": start, "end": end, "combined_bytes": combined,
                 "amplification": combined / max(1, end-start), "seed_mode": seed_mode,
                 "symbols_decoded": r.symbols_decoded, "recursive_calls": r.recursive_calls,
                 "max_depth": r.max_depth}
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
            "selected_seed_stored_bytes": selected_seed_bytes,
            "worst_pair_bytes_after_dispatch": cert_worst,
            "worst_fixed_probe_bytes": probe_worst,
            "pair_rows": pair_rows,
        })

    current_bytes = int(super_evidence["current_admission"]["stored_bytes"])
    v029_bytes = int(super_evidence["frozen_v029"]["stored_bytes"])
    sparse_grouped = int(super_evidence["superframe"]["stored_sparse_metadata_bytes"])
    candidate = current_bytes + sparse_grouped + total_selected_seed_bytes
    margin = v029_bytes - candidate
    supported = (
        exact_failures == 0
        and locality_failures == 0
        and certificate_failures == 0
        and margin > 0
    )

    cpu = time.process_time() - t0_cpu
    wall = time.perf_counter() - t0_wall
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
            "pair_certificates": total_pairs,
            "unsafe_pairs": total_unsafe_pairs,
            "available_seed_pages": total_available_seed_pages,
            "selected_seed_pages": total_selected_seed_pages,
            "selected_seed_stored_bytes": total_selected_seed_bytes,
            "seed_storage_fraction": total_selected_seed_bytes / max(1, sum(
                SEED._build_seeds(
                    DEP.parse_tokens(pool[manifest["stream_index"][h]["o"]:manifest["stream_index"][h]["o"]+manifest["stream_index"][h]["n"]]),
                    COLD._build_metadata(DEP.parse_tokens(pool[manifest["stream_index"][h]["o"]:manifest["stream_index"][h]["o"]+manifest["stream_index"][h]["n"]]))[0],
                    zlib.decompress(pool[manifest["stream_index"][h]["o"]:manifest["stream_index"][h]["o"]+manifest["stream_index"][h]["n"]], -15),
                )[1] for h in hashes
            )),
            "fixed_requests": fixed_requests,
            "exact_failures": exact_failures,
            "locality_failures": locality_failures,
            "certificate_failures": certificate_failures,
            "worst_fixed_probe": worst_probe,
            "worst_page_pair_certificate": worst_certificate,
            "max_symbols_decoded": max_symbols,
            "max_recursive_calls": max_recursive_calls,
            "max_recursion_depth": max_depth,
            "rows": rows,
        },
        "charged_economics": {
            "candidate_before_locality_metadata_bytes": current_bytes,
            "grouped_sparse_metadata_bytes": sparse_grouped,
            "selected_seed_metadata_bytes": total_selected_seed_bytes,
            "candidate_plus_gated_locality_bytes": candidate,
            "same_input_v029_bytes": v029_bytes,
            "margin_to_same_input_v029_bytes": margin,
        },
        "builder_profile": {
            "cpu_s_including_same_input_referee_and_certification": cpu,
            "wall_s_including_same_input_referee_and_certification": wall,
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
        "next_if_falsified": "preserve the branch-and-bound lower bound; compress/group only selected seed information or redesign restart state without moving 4KiB/8x semantics",
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
        "branch_and_bound": {k:v for k,v in d["branch_and_bound"].items() if k != "rows"},
        "charged_economics": d["charged_economics"],
        "builder_profile": d["builder_profile"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
