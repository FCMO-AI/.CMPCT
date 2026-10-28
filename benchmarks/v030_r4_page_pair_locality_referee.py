from __future__ import annotations

"""Exact page-pair referee for a tighter workload-independent v0.30 sparse-locality certificate.

Mission Lock / Referee
======================
The streaming earliest-root/span certificate is safe but rejected all eight exact Office SFV4 derived
streams at up to 34,580 B even though the exact unique closure of each first-rejected 4 KiB window was
only <=4,141 B. The gap is holes between sparse dependency chains.

A simple coverage theorem gives a stronger finite referee: every arbitrary request of at most 4 KiB is
contained in the union of at most two adjacent 4 KiB-aligned output pages. Dependency closure is
monotone under set inclusion, so if the exact unique transitive closure of every adjacent page pair is
<=32,768 bytes, then every arbitrary <=4 KiB request also has exact decoded dependency work <=32,768
bytes. This checks O(N/4096) supersets rather than every byte offset.

Falsifiable hypothesis: all exact Office SFV4 derived streams pass the adjacent-page-pair closure bound,
while the known exact-unsafe hostile streams (all-zero and repeated-row NPY payloads) are still rejected.
Known safe ramp and seeded-normal controls should pass. This is a diagnostic referee only; the full byte
parent graph is forbidden as shipping admission state, and decoded-work success does not gift physical
I/O, index bytes, authentication, recovery, seeks, or reader implementation cost.

Disproof: any Office page pair exceeds 32,768 B; any known unsafe hostile stream passes; or a known safe
control fails. Preserve that result instead of changing the 8x threshold.
"""

import argparse
from array import array
import json
import os
from pathlib import Path
import shutil
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_exact_stream_federation_v2 as SFV2
from benchmarks import v030_r4_office_sfv3_derived_views as SFV3
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from benchmarks import v030_r4_deflate_sparse_dependency_oracle as EXACT
from benchmarks import v030_r4_deflate_sparse_hostile_generalization as HOSTILE

SCHEMA = "cmpct-v030-r4-page-pair-locality-referee-v1"
PAGE = 4096
LIMIT = 8 * PAGE


def pair_referee(comp: bytes, raw: bytes) -> dict:
    parsed = EXACT.parse_parents(comp)
    parents = parsed["parents"]
    if len(parents) != len(raw) or zlib.decompress(comp, -15) != raw:
        raise RuntimeError("exact parser identity mismatch")
    marks = array("I", [0]) * len(parents)
    starts = list(range(0, max(1, len(raw)), PAGE))
    worst = None
    over = 0
    total = 0
    for generation, start in enumerate(starts, 1):
        end = min(start + 2 * PAGE, len(raw))
        row = EXACT.closure_for_request(parents, marks, generation, start, end)
        closure = row["unique_decoded_closure_bytes"]
        amp_vs_4k = closure / PAGE
        probe = {
            "page_start": start,
            "superwindow_end": end,
            "superwindow_bytes": end - start,
            "unique_decoded_closure_bytes": closure,
            "amplification_vs_max_4k_request": amp_vs_4k,
            "max_new_chain_depth": row["max_new_chain_depth"],
        }
        total += closure
        over += closure > LIMIT
        if worst is None or closure > worst["unique_decoded_closure_bytes"]:
            worst = probe
    if worst is None:
        raise RuntimeError("no page-pair probes")
    return {
        "decoded_bytes": len(raw),
        "pairs_checked": len(starts),
        "pairs_over_8x": over,
        "worst": worst,
        "mean_pair_closure_bytes": total / len(starts),
        "passes_every_arbitrary_le_4k_decoded_work_by_monotone_superset": over == 0,
        "parser": {
            "blocks": parsed["blocks"],
            "tokens": parsed["tokens"],
            "literal_tokens": parsed["literal_tokens"],
            "copy_tokens": parsed["copy_tokens"],
        },
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_page_pair_office_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_page_pair_office_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    containers, _shared = SFV2.discover(source)
    all_streams = SFV4._all_member_streams(containers)
    derived = SFV3._derived_inventory(source, containers, all_streams)
    if not derived:
        raise RuntimeError("no exact Office derived streams")

    office = []
    for rel, rec in sorted(derived.items()):
        comp = all_streams[rec["stream_hash"]]
        raw = (source / rel).read_bytes()
        r = pair_referee(comp, raw)
        office.append({"rel": rel, "compressed_bytes": len(comp), **r})

    # Keep the hostile-control contract explicit and fail closed on inventory drift. The first
    # page-pair run accidentally used stale *_npy labels while HOSTILE.cases() exposes *_f32 keys,
    # which misclassified the two known-unsafe controls as expected-safe despite the referee
    # correctly rejecting them. A changed control inventory must never silently alter the verdict.
    hostile_cases = HOSTILE.cases()
    hostile_expectations = {
        "all_zero_f32": True,
        "repeated_row_f32": True,
        "ramp_f32": False,
        "seeded_normal_f32": False,
    }
    if set(hostile_cases) != set(hostile_expectations):
        raise RuntimeError(
            "hostile control inventory drift: "
            f"cases={sorted(hostile_cases)} expected={sorted(hostile_expectations)}"
        )

    controls = []
    for name, raw in hostile_cases.items():
        comp = HOSTILE.raw_deflate(raw)
        r = pair_referee(comp, raw)
        controls.append(
            {
                "case": name,
                "expected_exact_unsafe": hostile_expectations[name],
                "compressed_bytes": len(comp),
                **r,
            }
        )

    office_fail = sum(r["pairs_over_8x"] > 0 for r in office)
    unsafe_missed = sum(r["expected_exact_unsafe"] and r["pairs_over_8x"] == 0 for r in controls)
    safe_rejected = sum((not r["expected_exact_unsafe"]) and r["pairs_over_8x"] > 0 for r in controls)
    supported = office_fail == 0 and unsafe_missed == 0 and safe_rejected == 0
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "page_bytes": PAGE,
        "frozen_decoded_work_limit_bytes": LIMIT,
        "theorem": "Every arbitrary <=4KiB request is contained in one adjacent aligned 8KiB page-pair superwindow; exact dependency closure is monotone under set inclusion.",
        "office": office,
        "controls": controls,
        "summary": {
            "office_streams": len(office),
            "office_streams_with_pair_over_8x": office_fail,
            "office_worst_pair_closure_bytes": max(r["worst"]["unique_decoded_closure_bytes"] for r in office),
            "office_worst_pair_amplification_vs_4k": max(r["worst"]["amplification_vs_max_4k_request"] for r in office),
            "known_unsafe_controls_missed": unsafe_missed,
            "known_safe_controls_rejected": safe_rejected,
        },
        "hypothesis": {"page_pair_referee_separates_office_opportunity_from_known_unsafe_streams": supported},
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "frozen_8x_limit": True,
            "threshold_sweep": False,
            "path_hash_workload_dispatch": False,
            "full_parent_graph_used_only_as_referee": True,
            "product_admission_authorized": False,
            "decoded_work_only": True,
            "physical_io_gifted": True,
            "auth_recovery_gifted": True,
            "metadata_gifted": True,
        },
        "next_if_supported": "build a compact streaming/capped page-pair certificate that reproduces this referee without a full parent graph; hostile-review it against the same unsafe controls before any Office selector integration",
        "next_if_falsified": "preserve the negative and change representation/framing; do not weaken the frozen 8x contract",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-page-pair-locality-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-page-pair-locality.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"summary": d["summary"], "hypothesis": d["hypothesis"], "controls": d["controls"]}, indent=2))


if __name__ == "__main__":
    main()
