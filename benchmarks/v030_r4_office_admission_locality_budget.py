from __future__ import annotations

"""Charge the existing sparse-anchor locality metadata against the v0.25-admission Office win.

Mission Lock
------------
The admission transfer stores 5,903,394 B, only 50,632 B below frozen v0.29 Office.
The prior SFV4 sparse cold-reader persisted 86,465 B of anchor/block metadata for the
streams needed by the eight derived views. Admission preserves all eight views, so the
falsifiable question is whether restricting the exact same locality representation to
the admitted stream universe reduces its persisted metadata below the 50,632 B density
headroom. No metadata representation, page size, codec, threshold, or locality law may
change in this referee.

Disproof: exact admitted candidate/tree/views differ from the prior admission receipt,
or sparse metadata >= density headroom. A pass grants no locality/release credit; it only
shows that the current index can coexist economically with v0.29-beating Office density.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from benchmarks import v030_r4_office_v025_admission_transfer as ADMIT
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-admission-locality-budget-v1"
ADMISSION_RECEIPT_BYTES = 5_903_394
V029_OFFICE_BYTES = SFV4.ACCEPTED_V029_OFFICE
HEADROOM = V029_OFFICE_BYTES - ADMISSION_RECEIPT_BYTES


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_admitlocal_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_admitlocal_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    expected = PRODUCT.treehash(source)

    out = work / "admission"
    cand = ADMIT._build_candidate(source, out, work / "admission-work")
    verify = SFV4.extract_candidate(out, work / "extract")
    if verify["tree_sha256"] != expected:
        raise RuntimeError("admission candidate tree mismatch")
    if cand["stored_bytes"] != ADMISSION_RECEIPT_BYTES:
        raise RuntimeError(f"admission receipt drift: {cand['stored_bytes']} != {ADMISSION_RECEIPT_BYTES}")
    if cand["derived_file_count"] != 8:
        raise RuntimeError("admission candidate no longer preserves all eight derived views")

    manifest = json.loads((out / "manifest.json").read_text())
    pool = (out / "streams.bin").read_bytes()
    hashes = sorted({rec["stream_hash"] for rec in manifest["derived"].values()})
    rows = []
    total = 0
    for h in hashes:
        s = manifest["stream_index"][h]
        comp = pool[s["o"]:s["o"]+s["n"]]
        parsed = DEP.parse_tokens(comp)
        raw = zlib.decompress(comp, -15)
        if parsed["output_bytes"] != len(raw):
            raise RuntimeError("DEFLATE parse/output mismatch")
        anchors, blocks, stored = COLD._build_metadata(parsed)
        total += stored
        rows.append({
            "stream_sha256": h,
            "compressed_bytes": len(comp),
            "raw_bytes": len(raw),
            "anchors": len(anchors),
            "block_states": len(blocks),
            "sparse_metadata_bytes": stored,
        })

    charged = cand["stored_bytes"] + total
    margin = V029_OFFICE_BYTES - charged
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "02_office_workspace",
        "tree_sha256": expected,
        "admission": {
            "stored_bytes": cand["stored_bytes"],
            "derived_files": cand["derived_file_count"],
            "admitted_containers": cand["admitted_containers"],
            "rejected_containers": cand["rejected_containers"],
        },
        "locality_metadata": {
            "unique_derived_streams": len(hashes),
            "rows": rows,
            "stored_bytes_including_per_frame_auth_directory": total,
        },
        "economics": {
            "frozen_v029_office_bytes": V029_OFFICE_BYTES,
            "pre_locality_headroom_bytes": HEADROOM,
            "candidate_plus_sparse_metadata_bytes": charged,
            "margin_to_v029_bytes": margin,
        },
        "hypothesis": {
            "exact_tree": verify["tree_sha256"] == expected,
            "all_eight_derived_views_preserved": cand["derived_file_count"] == 8,
            "current_sparse_metadata_fits_density_headroom": total < HEADROOM,
            "candidate_remains_below_v029_after_sparse_metadata": margin > 0,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "same_sparse_metadata_builder_as_prior_cold_reader": True,
            "fixed_page_bytes": COLD.PAGE,
            "fixed_8x_law": True,
            "no_parameter_or_codec_sweep": True,
            "remaining_debt": "physical reader still fails prior Office locality; page-seed/compact index, actual pread, auth-root integration, recovery, fresh-process CPU/RSS, native parity",
        },
        "next_if_supported": "combine admission with the existing physical-reader line and charge seeds/auth/pread exactly",
        "next_if_falsified": "preserve the density/locality collision; compact or eliminate locality metadata before any selector integration, without moving 4KiB/8x",
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-office-admission-locality-budget-work"))
    p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-office-admission-locality-budget.json"))
    a=p.parse_args(); d=run(a.work_root)
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n")
    print(json.dumps({"admission":d["admission"],"locality_metadata":{k:v for k,v in d["locality_metadata"].items() if k!='rows'},"economics":d["economics"],"hypothesis":d["hypothesis"]},sort_keys=True))

if __name__=="__main__": main()
