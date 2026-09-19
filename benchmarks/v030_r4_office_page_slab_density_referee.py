from __future__ import annotations

"""Fast density-only referee for the already-locked 4 KiB Office stream slab candidate.

This does not introduce a second hypothesis or tune any parameter.  It prices exactly
the same 4096-byte independently addressable STORE-vs-Zstd3 stream frames used by
v030_r4_office_page_slab_stream_store.py, on the complete all-member stream inventory.
It exists only to separate density feasibility from the slow 1,800-probe locality gate.

No release credit: selective locality is adjudicated exclusively by the full slab gate.
"""

import argparse
import json
import os
from pathlib import Path
import shutil

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_page_slab_stream_store as SLAB
from benchmarks import v030_r4_office_page_seed_cold_reader as SEED
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-page-slab-density-referee-v1"


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_slab_density_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_slab_density_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    built = SFV4.build_candidate(source, work / "sfv4", work / "sfv4-work")

    raw_stream_bytes = wrapped_stream_bytes = total_slabs = zstd_slabs = 0
    for _h, comp in built["all_streams"].items():
        slabs, stored = SLAB.build_slab_store(comp)
        raw_stream_bytes += len(comp)
        wrapped_stream_bytes += stored
        total_slabs += len(slabs)
        zstd_slabs += sum(r["codec"] == "zstd3" for r in slabs)
    if raw_stream_bytes != int(built["all_member_stream_bytes"]):
        raise RuntimeError("all-member stream accounting mismatch")

    # Recompute the exact locality metadata cost for all unique derived streams, without
    # executing any read.  This is the same builder path used by the full page-seed gate.
    sparse = seed = logical_seed = 0
    hashes = sorted({rec["stream_hash"] for rec in built["derived_inventory"].values()})
    for h in hashes:
        comp = built["all_streams"][h]
        raw = __import__("zlib").decompress(comp, -15)
        parsed = DEP.parse_tokens(comp)
        anchors, _blocks, sparse_stored = COLD._build_metadata(parsed)
        _seeds, seed_stored, seed_logical = SEED._build_seeds(parsed, anchors, raw)
        sparse += sparse_stored
        seed += seed_stored
        logical_seed += seed_logical

    sfv4 = int(built["stored_bytes"])
    nonstream = sfv4 - raw_stream_bytes
    candidate = nonstream + wrapped_stream_bytes + sparse + seed
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "02_office_workspace",
        "tree_sha256": PRODUCT.treehash(source),
        "fixed_candidate": {"slab_bytes": SLAB.SLAB, "zstd_level": SLAB.ZSTD_LEVEL, "slab_tax_bytes": SLAB.SLAB_TAX},
        "stream_store": {
            "raw_stream_bytes": raw_stream_bytes,
            "wrapped_stream_bytes": wrapped_stream_bytes,
            "saving_bytes": raw_stream_bytes - wrapped_stream_bytes,
            "total_slabs": total_slabs,
            "zstd_slabs": zstd_slabs,
            "stored_slabs": total_slabs - zstd_slabs,
        },
        "economics": {
            "sfv4_bytes": sfv4,
            "sfv4_nonstream_bytes": nonstream,
            "sparse_metadata_bytes": sparse,
            "seed_metadata_bytes": seed,
            "logical_seed_bytes": logical_seed,
            "candidate_with_locality_metadata_bytes": candidate,
            "accepted_v029_office_bytes": SFV4.ACCEPTED_V029_OFFICE,
            "margin_to_v029_bytes": SFV4.ACCEPTED_V029_OFFICE - candidate,
            "density_feasible": candidate < SFV4.ACCEPTED_V029_OFFICE,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "same_locked_candidate_as_full_gate": True,
            "no_parameter_sweep": True,
            "locality_credit": False,
            "note": "Full 1,800-probe slab gate alone adjudicates <=8x locality.",
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-slab-density-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-slab-density.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"stream_store": d["stream_store"], "economics": d["economics"]}, indent=2))


if __name__ == "__main__":
    main()
