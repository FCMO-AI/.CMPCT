from __future__ import annotations

"""All-15 PrefixGraph terminal-parity frontier.

Current shifted-version and boundary-churn rows spend roughly a minute waiting for G0-G4 even though PrefixGraph
is the final complete-artifact winner.  This oracle does not skip that work in production.  It builds PrefixGraph
independently and then the full release-candidate tournament on every frozen workload that PrefixGraph can
represent, proving exact winner bytes/tree and mapping conservative *PrefixGraph-internal* admission envelopes.

The envelopes use only facts available after the comparatively narrow PrefixGraph build: complete candidate bytes,
payload saving versus its all-direct floor, prefix-record count/density and measured <=8x locality.  They do not use
benchmark names or the expensive G0-G4 result as an admission input.  A zero-counterexample envelope is research
evidence for a later adversarial/generalization campaign, never permission to alter the shipping selector.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import time

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_prefixgraph as PG
from experiments import entropygraph_v030_release_candidate as RC

REL_THRESHOLDS = (0.0025, 0.005, 0.01, 0.02)
ABS_THRESHOLDS = (2048, 4096, 8192, 16384)
MIN_PREFIX_RECORDS = 2


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _corpora(work_root: Path):
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_pg_terminal_neutral",
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_pg_terminal_hostile",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_pg_terminal_repair")
    repair.install_generation_hooks(neutral)
    roots = []
    for suite, builder in (("neutral_hostile_v1", neutral), ("resemblance_hostile_v1", hostile)):
        root = work_root / suite
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        roots.append((suite, root))
    return accepted, roots


def _one(suite: str, source: Path, accepted: dict, root: Path) -> dict:
    name = source.name
    expected_tree = RC.treehash(source)
    eligible, reject = RC._prefixgraph_eligibility(source, expected_tree)
    row = {
        "label": f"{suite}/{name}",
        "eligible": eligible,
        "eligibility_reject_reason": reject,
        "accepted_v029_bytes": int(accepted[(suite, name)]["accepted_v029_bytes"]),
    }
    if not eligible:
        return row

    pg_path = root / "prefixgraph.cmpct"
    full_path = root / "full.cmpct"
    started = time.perf_counter()
    pg_stats = dict(PG.build(source, pg_path))
    pg_create = time.perf_counter() - started
    pg_verify = PG.strong_verify(pg_path)
    locality = RC._prefixgraph_locality(pg_path)
    if not pg_verify.get("ok") or pg_verify.get("tree_sha256") != PG.treehash(source):
        raise RuntimeError(f"PrefixGraph independent verification failed for {suite}/{name}")

    started = time.perf_counter()
    full = dict(RC.build(source, full_path, post_publish_verify=False, defer_preselection_verify=True))
    full_create = time.perf_counter() - started
    pg_bytes = pg_path.stat().st_size
    all_direct = int(pg_stats["all_direct_bytes"])
    saving = int(pg_stats["saving_vs_all_direct_bytes"])
    ratio = saving / max(1, all_direct)
    selected_pg = full["selected"] == "prefixgraph"
    exact_if_selected = (
        selected_pg
        and int(full["archive_bytes"]) == pg_bytes
        and _sha(full_path) == _sha(pg_path)
        and full["tree_sha256"] == expected_tree
    )
    row.update({
        "prefixgraph_bytes": pg_bytes,
        "prefixgraph_create_s": pg_create,
        "prefixgraph_all_direct_bytes": all_direct,
        "prefixgraph_payload_saving_bytes": saving,
        "prefixgraph_payload_saving_ratio": ratio,
        "prefix_records": int(pg_stats["prefix_records"]),
        "files": int(pg_stats["files"]),
        "anchor_auditions": int(pg_stats["anchor_auditions"]),
        "locality": locality,
        "full_selected": full["selected"],
        "full_bytes": int(full["archive_bytes"]),
        "full_create_s": full_create,
        "full_g04_bytes": int(full["g04_bytes"]),
        "prefixgraph_exact_full_winner": exact_if_selected,
        "observed_wait_elimination_s_if_terminal": max(0.0, full_create - pg_create) if exact_if_selected else 0.0,
    })
    return row


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted, roots = _corpora(work_root)
    rows = []
    for suite, root in roots:
        for source in sorted(path for path in root.iterdir() if path.is_dir()):
            expected = accepted[(suite, source.name)]["tree_sha256"]
            # The accepted repaired corpus is frozen in the release-candidate tree-hash domain.  The old
            # v0.29 benchmark helper no longer owns a treehash API; binding to it made this oracle die before
            # producing evidence.  Reuse the exact semantic owner used by PrefixGraph eligibility/selection.
            if RC.treehash(source) != expected:
                raise RuntimeError(f"frozen source drift for {suite}/{source.name}")
            with tempfile.TemporaryDirectory(prefix="cmpct-pg-terminal-row-", dir=work_root) as td:
                rows.append(_one(suite, source, accepted, Path(td)))
            print(json.dumps(rows[-1], separators=(",", ":")), flush=True)

    envelopes = []
    eligible_rows = [row for row in rows if row["eligible"]]
    for rel in REL_THRESHOLDS:
        for absolute in ABS_THRESHOLDS:
            admitted = [
                row for row in eligible_rows
                if row["locality"]["passed"]
                and row["prefix_records"] >= MIN_PREFIX_RECORDS
                and row["prefixgraph_payload_saving_bytes"] >= absolute
                and row["prefixgraph_payload_saving_ratio"] >= rel
            ]
            counterexamples = [row["label"] for row in admitted if not row["prefixgraph_exact_full_winner"]]
            envelopes.append({
                "relative_payload_saving_min": rel,
                "absolute_payload_saving_min": absolute,
                "minimum_prefix_records": MIN_PREFIX_RECORDS,
                "admitted": [row["label"] for row in admitted],
                "counterexamples": counterexamples,
                "zero_counterexamples": not counterexamples,
                "observed_wait_elimination_s": sum(row["observed_wait_elimination_s_if_terminal"] for row in admitted),
            })

    exact_winners = [row for row in eligible_rows if row.get("prefixgraph_exact_full_winner")]
    useful_safe = [env for env in envelopes if env["zero_counterexamples"] and env["admitted"]]
    gate = {
        "exact_workload_count": len(rows) == 15,
        "all_eligible_prefixgraph_verified": all(row["locality"]["passed"] for row in eligible_rows),
        "at_least_one_exact_prefixgraph_winner": bool(exact_winners),
        "envelope_matrix_complete": len(envelopes) == len(REL_THRESHOLDS) * len(ABS_THRESHOLDS),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-prefixgraph-terminal-parity-v1",
        "rows": rows,
        "envelopes": envelopes,
        "summary": {
            "eligible_rows": len(eligible_rows),
            "exact_prefixgraph_winners": [row["label"] for row in exact_winners],
            "safe_nonempty_envelopes": len(useful_safe),
            "best_observed_wait_elimination_s": max((env["observed_wait_elimination_s"] for env in useful_safe), default=0.0),
        },
        "gate": gate,
        "claim_boundary": (
            "Research-only terminal-parity map. Frozen-corpus zero-counterexample envelopes are hypotheses for a "
            "separate adversarial/generalization proof; they cannot modify release selection or authorize release."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-terminal-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-terminal.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "gate": result["gate"]}, indent=2))
    if not result["gate"]["passed"]:
        raise SystemExit("PrefixGraph terminal-parity measurement invalid")


if __name__ == "__main__":
    main()
