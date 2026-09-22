from __future__ import annotations

"""Exact-tree oracle for the v0.30 PrefixGraph depth-1 research seed.

The oracle is intentionally narrow.  It measures the two public workloads that falsify version-family
alignment assumptions and requires their regenerated trees *and* accepted v0.29 archive bytes to match the
immutable accepted evidence before a PrefixGraph saving can count.

The compact repository history intentionally stores only winning-row byte summaries, while the accepted
workflow artifact contains the full per-workload tree identities.  The two tree SHA-256 values below are
therefore frozen from accepted artifact 9281456150 / sha256:a25bdc766a0fb3630780337d4d430faed1e5f036bc8ea2155274b81c2c11db7e,
and the compact ledger is still read on every run to cross-check the accepted candidate byte counts.

Footnote: this is mechanism evidence, not a v0.30 release gate.  Geometry remains independently measured on
all 15 workloads; PrefixGraph may be composed only after this causal result is preserved.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

from benchmarks import resemblance_hostile_corpus_v1 as corpus
from experiments import entropygraph_v029_residual_strict as v029
from experiments import entropygraph_v030_prefixgraph as prefixgraph

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "benchmarks" / "history" / "2026-08-17-mosaic-v029-generalization-v3.json"
TARGETS = ("01_shifted_versions", "03_boundary_churn")
MIN_AGGREGATE_SAVING = 24 * 1024
MIN_EACH_SAVING = 2 * 1024
ACCEPTED_ARTIFACT = {
    "id": 9281456150,
    "digest": "sha256:a25bdc766a0fb3630780337d4d430faed1e5f036bc8ea2155274b81c2c11db7e",
    "workflow_run": 32008781417,
}
# Footnote: these are copied from the immutable accepted artifact's full `rows` payload because the compact
# committed history deliberately retains only winning-row byte summaries.  Keeping them explicit here makes
# future CI independent of artifact expiry while the ledger/artifact provenance remains machine-checkable.
ACCEPTED_TREE_SHA256 = {
    "01_shifted_versions": "d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd",
    "03_boundary_churn": "3238446efaef2a70a5c08d722bdc9dac3ac7c1c99ae3cde8093fae1481ad4b3d",
}


def _accepted_rows() -> dict[str, dict]:
    data = json.loads(HISTORY.read_text(encoding="utf-8"))
    artifact = data.get("artifact") or {}
    if artifact.get("id") != ACCEPTED_ARTIFACT["id"] or artifact.get("digest") != ACCEPTED_ARTIFACT["digest"]:
        raise RuntimeError("accepted v0.29 PrefixGraph artifact provenance drift")
    if data.get("workflow_run") != ACCEPTED_ARTIFACT["workflow_run"]:
        raise RuntimeError("accepted v0.29 PrefixGraph workflow provenance drift")

    rows = {}
    for row in data.get("winning_rows", []):
        name = row.get("name")
        if row.get("suite") == "resemblance_hostile_v1" and name in TARGETS:
            rows[name] = {
                "suite": row["suite"],
                "name": name,
                "candidate_bytes": int(row["candidate_bytes"]),
                "tree_sha256": ACCEPTED_TREE_SHA256[name],
            }
    if set(rows) != set(TARGETS):
        raise RuntimeError("accepted v0.29 PrefixGraph control rows are missing from compact history")
    return rows


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    source = work_root / "corpus"; source.mkdir()
    corpus.shifted_versions(source); corpus.boundary_churn(source)
    controls = _accepted_rows(); rows = []

    for name in TARGETS:
        tree = source / name; expected = controls[name]
        live_tree = prefixgraph.treehash(tree)
        if live_tree != expected["tree_sha256"]:
            raise RuntimeError(f"historical tree drift for {name}: {live_tree} != {expected['tree_sha256']}")

        base_path = work_root / f"{name}-v029.cmpct"; candidate_path = work_root / f"{name}-prefixgraph.cmpct"
        started = time.perf_counter(); base_stats = v029.build(tree, base_path); base_s = time.perf_counter() - started
        base_verify = v029.strong_verify(base_path)
        if not base_verify.get("ok") or base_verify.get("tree_sha256") != live_tree:
            raise RuntimeError(f"accepted v0.29 verification failed for {name}")
        if base_path.stat().st_size != int(expected["candidate_bytes"]):
            raise RuntimeError(
                f"accepted v0.29 byte drift for {name}: {base_path.stat().st_size} != {expected['candidate_bytes']}"
            )

        started = time.perf_counter(); pg_stats = prefixgraph.build(tree, candidate_path); pg_s = time.perf_counter() - started
        pg_verify = prefixgraph.strong_verify(candidate_path)
        if not pg_verify.get("ok") or pg_verify.get("tree_sha256") != live_tree:
            raise RuntimeError(f"PrefixGraph verification failed for {name}")

        base_bytes = base_path.stat().st_size; pg_bytes = candidate_path.stat().st_size
        selected_bytes = min(base_bytes, pg_bytes)
        row = {
            "name": name,
            "tree_sha256": live_tree,
            "v029_bytes": base_bytes,
            "prefixgraph_bytes": pg_bytes,
            "candidate_bytes": selected_bytes,
            "selected": "prefixgraph" if pg_bytes < base_bytes else "v029-fallback",
            "saving_vs_v029_bytes": base_bytes - selected_bytes,
            "raw_prefix_saving_vs_v029_bytes": base_bytes - pg_bytes,
            "prefix_records": int(pg_stats["prefix_records"]),
            "anchor": pg_stats["anchor"],
            "anchor_auditions": int(pg_stats["anchor_auditions"]),
            "max_dependency_depth": int(pg_stats["max_dependency_depth"]),
            "prefixgraph_create_s": pg_s,
            "v029_create_s": base_s,
            "v029_selected": base_stats.get("selected"),
        }
        print(json.dumps(row, sort_keys=True), flush=True); rows.append(row)

    saving = sum(row["saving_vs_v029_bytes"] for row in rows)
    totals = {
        "workloads": len(rows),
        "v029_bytes": sum(row["v029_bytes"] for row in rows),
        "candidate_bytes": sum(row["candidate_bytes"] for row in rows),
        "saving_vs_v029_bytes": saving,
        "workloads_improved": sum(row["saving_vs_v029_bytes"] > 0 for row in rows),
        "workloads_regressed": 0,
        "min_workload_saving_bytes": min(row["saving_vs_v029_bytes"] for row in rows),
        "max_dependency_depth": max(row["max_dependency_depth"] for row in rows),
        "mechanism_gate": (
            saving >= MIN_AGGREGATE_SAVING
            and all(row["saving_vs_v029_bytes"] >= MIN_EACH_SAVING for row in rows)
            and all(row["prefix_records"] > 0 for row in rows)
            and all(row["max_dependency_depth"] <= 1 for row in rows)
        ),
    }
    return {
        "schema": "cmpct-v030-prefixgraph-oracle-v1",
        "claim_boundary": "orthogonal two-workload mechanism oracle; canonical r24 unchanged",
        "contract": {
            "targets": list(TARGETS),
            "historical_control": str(HISTORY.relative_to(ROOT)),
            "accepted_artifact": ACCEPTED_ARTIFACT,
            "accepted_tree_sha256": ACCEPTED_TREE_SHA256,
            "minimum_aggregate_saving_bytes": MIN_AGGREGATE_SAVING,
            "minimum_each_workload_saving_bytes": MIN_EACH_SAVING,
            "max_dependency_depth": 1,
            "regression_tolerance_bytes": 0,
            "tree_and_v029_bytes_must_match_history": True,
        },
        "rows": rows,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/prefixgraph-v030-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/prefixgraph-v030-oracle.json"))
    args = parser.parse_args(); result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2), flush=True)
    if not result["totals"]["mechanism_gate"]:
        raise SystemExit("PrefixGraph failed frozen mechanism gate")


if __name__ == "__main__":
    main()
