"""F-01 causal/operator-liability experiment after the accepted O0.1 result.

Research-only.  This module removes operators from the already-frozen O0.1 grammar; it does not add
new vocabulary or change the accepted comparator/corpus.  Search wall time is gifted.  Every selected
program remains fully serialized and exact reconstruction remains mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from experiments import entropygraph_v030_reversible_structure_compiler_o01 as O
from experiments import entropygraph_v030_reversible_structure_compiler_o01_decisive as D

SCHEMA = "cmpct-v030-foundry-f01-causal-v1"
WITNESS_SEED = "c3ef298bcc3fb7f95a65245c9341f112581aa175"
WITNESS_CORPUS_FINGERPRINT = "6b6438aff98e7a9e69ee834fe3f2135cc03acde0babac42100c544519e56c574"
EXPECTED_WINNERS = {
    "discovery_mixed_lane_records": {
        "manual_bytes": 2090,
        "synthesized_bytes": 1538,
        "motif": "SPLIT@grid(LANE[8]+DELIM[10])",
    },
    "discovery_mixed_lane_widths": {
        "manual_bytes": 3086,
        "synthesized_bytes": 2525,
        "motif": "SPLIT@grid(LANE[8]+LANE[16])",
    },
    "transfer_postfreeze_mixed_shifted": {
        "manual_bytes": 1843,
        "synthesized_bytes": 1416,
        "motif": "SPLIT@grid(LANE[8]+DELIM[103])",
    },
}


def _decisive_discovery() -> list[tuple[str, bytes]]:
    cases = list(O._discovery_cases())
    left = O._lane_block(8192, 8, 73)[:49152]
    right = O._lane_block(4096, 16, 91)[:49152]
    cases.append(("discovery_mixed_lane_widths", left + right))
    return cases


def _corpus_fingerprint(cases: list[tuple[str, bytes]]) -> str:
    manifest = [
        {"case": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        for name, raw in cases
    ]
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _all_cases() -> list[tuple[str, bytes]]:
    return _decisive_discovery() + O._hostile_cases() + O._transfer_cases(WITNESS_SEED)


def _remove_from_alternatives(remove: str):
    original = O._alternatives

    def filtered(raw: bytes, stats: dict[str, int]):
        candidates = original(raw, stats)
        if remove == "LANE":
            return [c for c in candidates if not c.motif.startswith("LANE[")]
        if remove == "DELIM":
            return [c for c in candidates if not c.motif.startswith("DELIM[")]
        if remove.startswith("LANE["):
            return [c for c in candidates if c.motif != remove]
        raise ValueError(f"unsupported F-01 causal ablation {remove}")

    return original, filtered


def _search_without(raw: bytes, remove: str) -> dict:
    original, filtered = _remove_from_alternatives(remove)
    O._alternatives = filtered
    try:
        result = O.search(raw)
    finally:
        O._alternatives = original
    if not result["exact_reconstruction"]:
        raise RuntimeError(f"F-01 causal ablation lost exact reconstruction: {remove}")
    return result


def _families(motif: str) -> list[str]:
    out = ["SPLIT"] if motif.startswith("SPLIT") else []
    if "LANE[" in motif:
        out.append("LANE")
    if "DELIM[" in motif:
        out.append("DELIM")
    return out


def run(source_commit: str) -> dict:
    accepted = D.run(WITNESS_SEED)
    discovery_hostile = _decisive_discovery() + O._hostile_cases()
    observed_fingerprint = _corpus_fingerprint(discovery_hostile)
    case_bytes = dict(_all_cases())
    accepted_by_name = {case["case"]: case for case in accepted["cases"]}

    conflicts: list[str] = []
    if accepted.get("schema") != "cmpct-v030-foundry-f01-o01-v2":
        conflicts.append("accepted_schema_mismatch")
    if accepted.get("decision") != "ADVANCE_COMPOSITION":
        conflicts.append("accepted_decision_mismatch")
    if observed_fingerprint != WITNESS_CORPUS_FINGERPRINT:
        conflicts.append("corpus_fingerprint_mismatch")
    if accepted.get("corpus_fingerprint") != WITNESS_CORPUS_FINGERPRINT:
        conflicts.append("accepted_receipt_fingerprint_mismatch")

    causal: dict[str, dict] = {}
    for name, expected in EXPECTED_WINNERS.items():
        base = accepted_by_name.get(name)
        if base is None:
            conflicts.append(f"missing_winner:{name}")
            continue
        for key, value in (
            ("manual_bytes", expected["manual_bytes"]),
            ("synthesized_bytes", expected["synthesized_bytes"]),
            ("synthesized_motif", expected["motif"]),
        ):
            if base.get(key) != value:
                conflicts.append(f"accepted_witness_mismatch:{name}:{key}")
        if not base.get("exact_reconstruction"):
            conflicts.append(f"accepted_reconstruction_failure:{name}")
        raw = case_bytes[name]
        row = {
            "accepted_manual_bytes": base["manual_bytes"],
            "accepted_bytes": base["synthesized_bytes"],
            "accepted_motif": base["synthesized_motif"],
            "accepted_gain_bytes": base["manual_bytes"] - base["synthesized_bytes"],
            "ablations": {},
        }
        # SPLIT removal is exactly the frozen one-stage manual frontier.
        row["ablations"]["SPLIT"] = {
            "best_bytes": base["manual_bytes"],
            "best_motif": base["manual_motif"],
            "unique_contribution_bytes": base["manual_bytes"] - base["synthesized_bytes"],
            "restores_manual_control": True,
            "exact_reconstruction": True,
        }
        for family in _families(base["synthesized_motif"]):
            if family == "SPLIT":
                continue
            ablated = _search_without(raw, family)
            row["ablations"][family] = {
                "best_bytes": ablated["synthesized_bytes"],
                "best_motif": ablated["synthesized_motif"],
                "unique_contribution_bytes": ablated["synthesized_bytes"] - base["synthesized_bytes"],
                "restores_manual_control": ablated["synthesized_bytes"] == base["manual_bytes"],
                "exact_reconstruction": ablated["exact_reconstruction"],
            }
        causal[name] = row

    lane_width_liability: dict[str, dict] = {}
    all_names = [name for name, _ in _all_cases()]
    for width in O.L.LANE_WIDTHS:
        remove = f"LANE[{width}]"
        changed: list[dict] = []
        for name in all_names:
            raw = case_bytes[name]
            base = O.search(raw)
            ablated = _search_without(raw, remove)
            if (
                base["synthesized_bytes"] != ablated["synthesized_bytes"]
                or base["synthesized_motif"] != ablated["synthesized_motif"]
            ):
                changed.append({
                    "case": name,
                    "base_bytes": base["synthesized_bytes"],
                    "ablated_bytes": ablated["synthesized_bytes"],
                    "base_motif": base["synthesized_motif"],
                    "ablated_motif": ablated["synthesized_motif"],
                })
        lane_width_liability[str(width)] = {
            "changed_cases": changed,
            "scoped_search_liability": not changed,
        }

    if conflicts:
        decision = "CAUSAL_RESULT_CONFLICT"
    else:
        simpler = False
        for row in causal.values():
            split = row["ablations"]["SPLIT"]
            if split["unique_contribution_bytes"] <= 0 or not split["restores_manual_control"]:
                conflicts.append("split_ablation_did_not_restore_manual")
                decision = "CAUSAL_RESULT_CONFLICT"
                break
            for family, ablation in row["ablations"].items():
                if family == "SPLIT":
                    continue
                if ablation["unique_contribution_bytes"] <= 0:
                    simpler = True
        else:
            decision = "SIMPLER_PRIMITIVE_SIGNAL" if simpler else "CAUSAL_SEED"

    return {
        "schema": SCHEMA,
        "source_commit": source_commit,
        "o01_witness_seed": WITNESS_SEED,
        "o01_corpus_fingerprint": observed_fingerprint,
        "o01_artifact_digest": "sha256:3c4a5ed2195e8f9e0d3937a4f12863645e8f8bd152a49dc615dcac056f881323",
        "decision": decision,
        "conflicts": conflicts,
        "causal_winners": causal,
        "lane_width_liability": lane_width_liability,
        "oracle_gift_ledger": {
            "gifted": ["ablation search wall time"],
            "never_gifted": ["program/control bytes", "terminal bytes", "exact reconstruction", "accepted witness bytes"],
            "deferred_debt": [
                "generic admission economics", "canonical framing/index", "whole-archive locality",
                "recovery/integrity", "hostile parser/fuzz", "native/platform", "product runtime",
                "addressable opportunity mass", "global mechanism carrying cost",
            ],
        },
        "strongest_surviving_objection": (
            "Even causal split/transform necessity on these witnesses may indicate only a small distilled mixed-structure "
            "primitive, not a general compiler worth canonical reader complexity."
        ),
        "next_decisive_test": (
            "If CAUSAL_SEED, freeze structurally varied transfer plus AOM/carrying-cost measurement before any O0.2 vocabulary expansion."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", default=os.environ.get("EVIDENCE_HEAD", ""))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.source_commit or len(args.source_commit) < 12:
        raise SystemExit("F-01 causal ablation requires exact source commit")
    result = run(args.source_commit)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
