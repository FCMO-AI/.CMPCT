from __future__ import annotations

"""Focused exact-generator payload falsifier for v0.30 Bitplane Algebra.

This probe deliberately separates prior-art value from CMPCT-specific algebraic value:

Geometry incumbent -> best plain bitplane -> best screened predictor/basis bitplane.

The benchmark operates on complete deterministic public *files* split only by the inherited <=512 KiB balanced
node ceiling.  It does not trust the file extension to choose a transform; filenames are used only by this
benchmark harness to report which public control was measured.  The transform receives bytes alone.

Claim boundary: detached physical-node payload evidence, not a CMPCT archive-size claim.  Passing justifies a
later authenticated GIR integration; it does not authorize merge/version/release work.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from benchmarks import neutral_hostile_corpus_v1 as neutral
from experiments import entropygraph_v030_bitplane_algebra as BPA
from experiments import entropygraph_v030_bitplane_algebra_safe as SAFE

EXPECTED_TREES = {
    "04_analytics_and_database": "6d0854fe058a95258588b89dca653ac8f00c61f815c6127b179e86cc58b1789d",
    "09_ml_artifacts": "efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d",
}
TARGETS = (
    ("04_analytics_and_database", "features.npy", "numeric"),
    ("04_analytics_and_database", "features_compressed.npz", "already-compressed-control"),
    ("09_ml_artifacts", "scales.npy", "numeric"),
    ("09_ml_artifacts", "model.q4.bin", "high-entropy-control"),
)
MIN_SINGLE_FILE_SAVING = 64 * 1024
MIN_AGGREGATE_SAVING = 128 * 1024


def _generate(parent: Path) -> dict[str, Path]:
    shutil.rmtree(parent, ignore_errors=True)
    parent.mkdir(parents=True)
    neutral.corpus_analytics(parent)
    neutral.corpus_ml(parent)
    roots = {
        name: parent / name
        for name in EXPECTED_TREES
    }
    for name, root in roots.items():
        got = neutral.tree_hash(root)
        if got != EXPECTED_TREES[name]:
            raise RuntimeError(f"BPA source identity drift for {name}: expected {EXPECTED_TREES[name]}, got {got}")
    return roots


def _zstd_payload(transformed: bytes) -> bytes:
    payload = BPA.G.zc(transformed, BPA.EXACT_LEVEL)
    return payload if len(payload) < len(transformed) else transformed


def _plain_bitplane_best(raw: bytes, ceiling: int) -> dict:
    """Price prior-art bitshuffle alone, using the same inferred alignment surface.

    Footnote: this decomposition runs only after the full BPA oracle selects a winner.  Controls that fall back
    do not pay a second expensive transform tournament merely to prove again that no candidate was selected.
    """
    best = {"payload_bytes": ceiling, "width": None, "alignment": None}
    for width in BPA.WORD_WIDTHS:
        for alignment in BPA.rank_alignments(raw, width):
            try:
                transformed = BPA.forward(raw, width, alignment, "identity", ("none", 0))
            except ValueError:
                continue
            if BPA.inverse(transformed, len(raw)) != raw:
                raise RuntimeError("plain bitplane decomposition failed exact inverse")
            payload = _zstd_payload(transformed)
            rank = (len(payload), width, alignment)
            incumbent = (
                int(best["payload_bytes"]),
                int(best["width"]) if best["width"] is not None else 1 << 30,
                int(best["alignment"]) if best["alignment"] is not None else 1 << 30,
            )
            if rank < incumbent:
                best = {"payload_bytes": len(payload), "width": width, "alignment": alignment}
    return best


def _run_file(path: Path, role: str) -> dict:
    raw = path.read_bytes()
    chunks = BPA.G.L._balanced_chunks(raw)
    rows = []
    for index, chunk in enumerate(chunks):
        result = SAFE.audition(chunk)
        candidate_bytes = int(result["payload_bytes"])
        saving = int(result["saving_vs_incumbent_bytes"])
        incumbent_bytes = candidate_bytes + saving
        plain = None
        algebra_extra = 0
        if result["kind"] == "bitplane-algebra":
            plain = _plain_bitplane_best(chunk, incumbent_bytes)
            algebra_extra = int(plain["payload_bytes"]) - candidate_bytes
        rows.append({
            "chunk": index,
            "logical_bytes": len(chunk),
            "incumbent_kind": result["incumbent_kind"],
            "incumbent_payload_bytes": incumbent_bytes,
            "candidate_kind": result["kind"],
            "candidate_payload_bytes": candidate_bytes,
            "saving_vs_geometry_bytes": saving,
            "plain_bitplane": plain,
            "algebra_extra_vs_plain_bitplane_bytes": algebra_extra,
            "width": result["width"],
            "alignment": result["alignment"],
            "predictor": result["predictor"],
            "basis": result["basis"],
            "screened_candidates": result["screened_candidates"],
            "exact_finalists": result["exact_finalists"],
        })

    incumbent_total = sum(row["incumbent_payload_bytes"] for row in rows)
    candidate_total = sum(row["candidate_payload_bytes"] for row in rows)
    saving_total = incumbent_total - candidate_total
    algebra_extra_total = sum(max(0, row["algebra_extra_vs_plain_bitplane_bytes"]) for row in rows)
    return {
        "file": path.name,
        "role": role,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "logical_bytes": len(raw),
        "chunks": len(rows),
        "geometry_payload_bytes": incumbent_total,
        "bpa_payload_bytes": candidate_total,
        "saving_vs_geometry_bytes": saving_total,
        "smaller_than_geometry_pct": saving_total / max(1, incumbent_total) * 100.0,
        "bpa_selected_chunks": sum(row["candidate_kind"] == "bitplane-algebra" for row in rows),
        "algebra_extra_vs_plain_bitplane_bytes": algebra_extra_total,
        "max_exact_finalists": max((row["exact_finalists"] for row in rows), default=0),
        "rows": rows,
    }


def run(work_root: Path) -> dict:
    roots = _generate(work_root / "corpora")
    files = []
    for workload, rel, role in TARGETS:
        path = roots[workload] / rel
        if not path.is_file():
            raise RuntimeError(f"missing frozen BPA target: {path}")
        row = _run_file(path, role)
        row["workload"] = workload
        files.append(row)

    saving = sum(row["saving_vs_geometry_bytes"] for row in files)
    numeric = [row for row in files if row["role"] == "numeric"]
    totals = {
        "files": len(files),
        "geometry_payload_bytes": sum(row["geometry_payload_bytes"] for row in files),
        "bpa_payload_bytes": sum(row["bpa_payload_bytes"] for row in files),
        "saving_vs_geometry_bytes": saving,
        "max_single_file_saving_bytes": max(row["saving_vs_geometry_bytes"] for row in files),
        "files_improved": sum(row["saving_vs_geometry_bytes"] > 0 for row in files),
        "files_regressed": sum(row["saving_vs_geometry_bytes"] < 0 for row in files),
        "bpa_selected_chunks": sum(row["bpa_selected_chunks"] for row in files),
        "algebra_extra_vs_plain_bitplane_bytes": sum(row["algebra_extra_vs_plain_bitplane_bytes"] for row in files),
        "max_exact_finalists": max(row["max_exact_finalists"] for row in files),
        "mechanism_gate": (
            saving >= MIN_AGGREGATE_SAVING
            and max(row["saving_vs_geometry_bytes"] for row in numeric) >= MIN_SINGLE_FILE_SAVING
            and all(row["saving_vs_geometry_bytes"] >= 0 for row in files)
            and any(row["bpa_selected_chunks"] > 0 for row in numeric)
        ),
    }
    return {
        "schema": "cmpct-v030-bitplane-algebra-probe-v1",
        "status": "CHILD_RESEARCH_PAYLOAD_ORACLE_NOT_RELEASE",
        "claim_boundary": (
            "Exact public-generator file bytes; detached <=512 KiB physical-node payload accounting only. "
            "Existing safe G0/G1/G2 Geometry is the direct incumbent. No complete CMPCT archive claim."
        ),
        "prior_art_boundary": (
            "plain_bitplane reports Bitshuffle-like value; algebra_extra_vs_plain_bitplane reports only the "
            "additional value of predictor/basis candidates beyond that prior-art transform."
        ),
        "contract": {
            "expected_trees": EXPECTED_TREES,
            "targets": list(TARGETS),
            "minimum_single_numeric_file_saving_bytes": MIN_SINGLE_FILE_SAVING,
            "minimum_aggregate_saving_bytes": MIN_AGGREGATE_SAVING,
            "regression_tolerance_bytes": 0,
            "max_exact_finalists": BPA.MAX_EXACT_FINALISTS,
            "algebra_submechanism_rule": (
                "Algebraic predictor/basis novelty is retained only if measured algebra_extra_vs_plain_bitplane_bytes "
                "is material; otherwise retain plain bitplane as SOTA and reject the algebraic submechanism."
            ),
        },
        "files": files,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
