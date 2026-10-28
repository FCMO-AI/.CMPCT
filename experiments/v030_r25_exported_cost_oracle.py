from __future__ import annotations

"""Exact exported-cost attribution for canonical CMPCT revision 25.

The canonical 15-workload gate currently shows several rows where the internal G0-G4 candidate is nearly
byte-identical to the accepted v0.29 research floor but the final canonical product is materially larger.  This
research oracle asks where those bytes enter.  It executes the real release-product builder on the exact repaired
15-workload corpus and records only already-produced product facts plus an independently measured filesystem-
control size.  It changes no product code, selector, grammar, benchmark floor, threshold, or admission rule and
receives zero release credit.

The decisive diagnostic quantities are, per workload:
  accepted-v0.29 -> internal G0-G4 -> canonical r25 complete artifact -> genuine canonical r24 -> published product
and the filesystem-v1 / admitted implicit-v4 control sizes.  This distinguishes missing compression capability
from productization/semantic-carrying cost without pretending an oracle is a shipping win.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_release_generalization as GATE
from experiments import entropygraph_v030_release_product as CANON
from experiments import entropygraph_v030_r25_manifest_admission as MANIFEST

ENGINE = "v030-r25-exported-cost-oracle-v1"


def _filesystem_control(root: Path) -> dict:
    raw, _regular, stats = CANON.FS.capture_filesystem_manifest(
        Path(root),
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_profile_files=CANON.MAX_PROFILE_FILES,
        max_profile_logical_bytes=CANON.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    admitted = MANIFEST.admit(
        raw,
        max_path_bytes=CANON.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANON.MAX_MANIFEST_ENTRIES,
    )
    return {
        "filesystem_v1_bytes": len(raw),
        "filesystem_v1_sha256": hashlib.sha256(raw).hexdigest(),
        "selected_encoding": admitted.encoding,
        "selected_bytes": admitted.selected_bytes,
        "saving_bytes": admitted.saving_bytes,
        "entries": int(stats["entries"]),
        "regular_graph_members": int(stats["regular_graph_members"]),
        "logical_regular_bytes": int(stats["logical_regular_bytes"]),
    }


def _row(suite: str, root: Path, accepted: dict, out: Path) -> dict:
    key = (suite, root.name)
    expected = accepted[key]
    historical_tree = GATE._historical_treehash(root)
    if historical_tree != expected["tree_sha256"]:
        raise RuntimeError(
            f"historical source drift for {suite}/{root.name}: "
            f"{historical_tree} != {expected['tree_sha256']}"
        )

    control = _filesystem_control(root)
    product = dict(CANON.build(root, out))
    verified = CANON.strong_verify(out)
    if not verified.get("ok"):
        raise RuntimeError(f"canonical product strong verification failed for {suite}/{root.name}: {verified!r}")

    r25 = product.get("r25") if isinstance(product.get("r25"), dict) else {}
    accepted_bytes = int(expected["accepted_v029_bytes"])
    published = int(product["archive_bytes"])
    r24 = product.get("r24_product_bytes")
    r25_complete = product.get("r25_product_bytes")
    g04 = r25.get("g04_bytes")
    pg = r25.get("prefixgraph_bytes")

    def integer(value):
        return int(value) if isinstance(value, int) and not isinstance(value, bool) else None

    r24 = integer(r24)
    r25_complete = integer(r25_complete)
    g04 = integer(g04)
    pg = integer(pg)
    return {
        "suite": suite,
        "name": root.name,
        "historical_tree_sha256": historical_tree,
        "accepted_v029_bytes": accepted_bytes,
        "g04_bytes": g04,
        "g04_delta_vs_v029_bytes": None if g04 is None else g04 - accepted_bytes,
        "prefixgraph_bytes": pg,
        "r25_complete_bytes": r25_complete,
        "r25_exported_delta_vs_g04_bytes": (
            None if r25_complete is None or g04 is None else r25_complete - g04
        ),
        "r25_delta_vs_v029_bytes": None if r25_complete is None else r25_complete - accepted_bytes,
        "r24_complete_bytes": r24,
        "r24_delta_vs_v029_bytes": None if r24 is None else r24 - accepted_bytes,
        "published_bytes": published,
        "published_delta_vs_v029_bytes": published - accepted_bytes,
        "selected": product.get("selected"),
        "format_revision": product.get("format_revision"),
        "format_profile": product.get("format_profile"),
        "r25_attempted": bool(product.get("r25_attempted", False)),
        "r25_candidate_profile": product.get("r25_candidate_profile"),
        "r25_candidate_is_canonical": bool(product.get("r25_candidate_is_canonical", False)),
        "r25_strictly_smaller_than_r24": bool(product.get("r25_strictly_smaller_than_r24", False)),
        "r25_strictly_smaller_than_v029_research_floor": bool(
            product.get("r25_strictly_smaller_than_v029_research_floor", False)
        ),
        "v029_research_floor_bytes": integer(product.get("v029_research_floor_bytes")),
        "r25_internal_selected": r25.get("selected"),
        "r25_internal_g04_selected": r25.get("g04_selected"),
        "r25_internal_prefixgraph_admitted": bool(r25.get("prefixgraph_admitted", False)),
        "r25_internal_prefixgraph_reject_reason": r25.get("prefixgraph_reject_reason"),
        "filesystem_control": control,
        "published_strong_verify": {
            "ok": bool(verified.get("ok")),
            "format_revision": verified.get("format_revision"),
            "format_profile": verified.get("format_profile"),
            "tree_sha256": verified.get("tree_sha256"),
        },
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GATE._accepted_v029_rows()
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_r25_cost_neutral")
    hostile = V029._load(V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v030_r25_cost_hostile")
    repair = V029._load(V029.REPAIR_PATH, "cmpct_v030_r25_cost_repair_v6")
    repair.install_generation_hooks(neutral)

    rows = []
    for suite, corpus, root in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ):
        corpus.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            out = work_root / "archives" / suite / f"{workload.name}.cmpct"
            out.parent.mkdir(parents=True, exist_ok=True)
            row = _row(suite, workload, accepted, out)
            rows.append(row)
            print(json.dumps({
                "suite": suite,
                "name": workload.name,
                "v029": row["accepted_v029_bytes"],
                "g04": row["g04_bytes"],
                "r25": row["r25_complete_bytes"],
                "r24": row["r24_complete_bytes"],
                "published": row["published_bytes"],
                "selected": row["selected"],
                "control": row["filesystem_control"],
            }), flush=True)

    if len(rows) != 15:
        raise RuntimeError(f"expected 15 workloads, got {len(rows)}")

    def total(field: str) -> int | None:
        values = [row[field] for row in rows]
        return None if any(value is None for value in values) else sum(int(value) for value in values)

    accepted_total = sum(int(row["accepted_v029_bytes"]) for row in rows)
    g04_total = total("g04_bytes")
    r25_total = total("r25_complete_bytes")
    r24_total = total("r24_complete_bytes")
    published_total = sum(int(row["published_bytes"]) for row in rows)
    totals = {
        "accepted_v029_bytes": accepted_total,
        "g04_bytes": g04_total,
        "g04_delta_vs_v029_bytes": None if g04_total is None else g04_total - accepted_total,
        "r25_complete_bytes": r25_total,
        "r25_delta_vs_v029_bytes": None if r25_total is None else r25_total - accepted_total,
        "r25_exported_delta_vs_g04_bytes": (
            None if r25_total is None or g04_total is None else r25_total - g04_total
        ),
        "r24_complete_bytes": r24_total,
        "r24_delta_vs_v029_bytes": None if r24_total is None else r24_total - accepted_total,
        "published_bytes": published_total,
        "published_delta_vs_v029_bytes": published_total - accepted_total,
        "filesystem_v1_bytes": sum(row["filesystem_control"]["filesystem_v1_bytes"] for row in rows),
        "filesystem_selected_bytes": sum(row["filesystem_control"]["selected_bytes"] for row in rows),
        "filesystem_control_saving_bytes": sum(row["filesystem_control"]["saving_bytes"] for row in rows),
        "r25_canonical_rows": sum(row["r25_candidate_is_canonical"] for row in rows),
        "r25_beats_v029_rows": sum(row["r25_strictly_smaller_than_v029_research_floor"] for row in rows),
        "r25_beats_r24_rows": sum(row["r25_strictly_smaller_than_r24"] for row in rows),
        "published_r25_rows": sum(row["format_revision"] == 25 for row in rows),
        "published_r24_rows": sum(row["format_revision"] == 24 for row in rows),
    }
    return {
        "engine": ENGINE,
        "evidence_class": "research-oracle",
        "product_release_credit": False,
        "claim": "exact canonical r25/r24 exported-cost attribution on the frozen 15-workload substrate",
        "contract": {
            "workloads": 15,
            "accepted_v029_aggregate_bytes": GATE.EXPECTED_V029_TOTAL,
            "release_thresholds_unchanged": True,
            "product_selector_unchanged": True,
            "product_grammar_unchanged": True,
        },
        "totals": totals,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/r25-exported-cost-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/r25-exported-cost.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2), flush=True)


if __name__ == "__main__":
    main()
