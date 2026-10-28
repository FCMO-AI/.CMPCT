from __future__ import annotations

"""Same-input Office admission + sparse-locality economic referee.

This removes historical byte totals from the locality-budget decision. One repaired,
filesystem-metadata-stable Office tree is given to the current admission mechanism and
to the frozen source-sealed v0.29 product. The exact admitted derived streams are then
charged with the *unchanged* 4 KiB sparse-anchor/block representation from the prior
cold-reader line.

Hypothesis
----------
The current independently framed sparse representation fits inside the direct same-input
v0.30 density margin over v0.29.

Disproof
--------
If candidate + sparse metadata is not smaller than frozen v0.29 on the exact same tree,
the representation is economically incompatible with the density win. No threshold,
page size, codec, authentication tax, or locality law may be changed here.

Green CI means faithful measurement; the density/locality-budget verdict lives in JSON.
No physical locality or release credit is granted by this referee.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import zlib

from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_admission_same_input_v029_referee as SAME

SCHEMA = "cmpct-v030-r4-office-same-input-sparse-budget-v1"


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    source = SAME._build_source(work)

    _cand, current = SAME._build_current(source, work / "current", work / "current-work")
    current_repeat = SAME._build_current(source, work / "current-repeat", work / "current-repeat-work")[1]
    if current["component_sha256"] != current_repeat["component_sha256"]:
        raise RuntimeError("current repaired admission candidate is not byte-deterministic")

    frozen = SAME._run_v029(worker, v029_checkout, source, work / "frozen")
    if not frozen.get("source_sealed") or not frozen.get("reconstruction_exact"):
        raise RuntimeError("frozen v0.29 comparator seal/exactness failure")

    manifest = json.loads((work / "current" / "manifest.json").read_text())
    pool = (work / "current" / "streams.bin").read_bytes()
    hashes = sorted({rec["stream_hash"] for rec in manifest["derived"].values()})
    rows = []
    sparse_total = 0
    body_total = 0
    frame_tax_total = 0
    records_total = 0
    for h in hashes:
        s = manifest["stream_index"][h]
        comp = pool[s["o"] : s["o"] + s["n"]]
        parsed = DEP.parse_tokens(comp)
        raw = zlib.decompress(comp, -15)
        if parsed["output_bytes"] != len(raw):
            raise RuntimeError("DEFLATE parse/output mismatch")
        anchors, blocks, stored = COLD._build_metadata(parsed)
        records = len(anchors) + len(blocks)
        tax = records * COLD.FRAME_TAX
        body = stored - tax
        if body < 0:
            raise RuntimeError("sparse metadata body accounting underflow")
        sparse_total += stored
        body_total += body
        frame_tax_total += tax
        records_total += records
        rows.append({
            "stream_sha256": h,
            "compressed_bytes": len(comp),
            "raw_bytes": len(raw),
            "anchors": len(anchors),
            "block_states": len(blocks),
            "records": records,
            "compressed_record_body_bytes": body,
            "per_record_auth_directory_tax_bytes": tax,
            "stored_sparse_metadata_bytes": stored,
        })

    direct_margin = int(frozen["stored_bytes"]) - current["stored_bytes"]
    charged = current["stored_bytes"] + sparse_total
    charged_margin = int(frozen["stored_bytes"]) - charged
    verdict = charged_margin > 0

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "source": {
            "tree_sha256": current["tree_sha256"],
            "fixed_epoch_ns": SAME.MTIME.FIXED_EPOCH_NS,
        },
        "current_admission": current,
        "frozen_v029": frozen,
        "direct_same_input_density": {
            "current_bytes": current["stored_bytes"],
            "v029_bytes": int(frozen["stored_bytes"]),
            "current_margin_bytes": direct_margin,
        },
        "sparse_metadata": {
            "unique_derived_streams": len(hashes),
            "records": records_total,
            "compressed_record_body_bytes": body_total,
            "per_record_auth_directory_tax_bytes": frame_tax_total,
            "stored_bytes": sparse_total,
            "rows": rows,
        },
        "charged_economics": {
            "candidate_plus_sparse_metadata_bytes": charged,
            "margin_to_same_input_v029_bytes": charged_margin,
        },
        "hypothesis": {
            "current_candidate_byte_deterministic": current["component_sha256"] == current_repeat["component_sha256"],
            "current_smaller_than_v029_before_locality_metadata": direct_margin > 0,
            "current_individual_frame_sparse_metadata_fits_same_input_margin": verdict,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "same_sparse_metadata_builder": True,
            "fixed_page_bytes": COLD.PAGE,
            "fixed_8x_law": True,
            "frame_tax_bytes_per_record": COLD.FRAME_TAX,
            "frozen_v029_source_sealed": True,
            "no_parameter_or_codec_sweep": True,
        },
        "next_if_supported": "combine with the physical reader and charge seeds/pread/auth-root/recovery/CPU/RSS before admission",
        "next_if_falsified": "preserve the collision and test authenticated metadata grouping that keeps the same information while amortizing proof traffic; do not move the 4KiB/8x law",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-same-input-sparse-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-same-input-sparse.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "direct_same_input_density": d["direct_same_input_density"],
        "sparse_metadata": {k: v for k, v in d["sparse_metadata"].items() if k != "rows"},
        "charged_economics": d["charged_economics"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
