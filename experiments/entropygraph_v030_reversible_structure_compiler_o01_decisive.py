"""Decisive evidence wrapper for the frozen F-01/O0.1 grammar.

This file does not add an operator or change program charging/search semantics.  It fixes two
pre-result evidence-contract defects found by hostile review: the preregistered corpus fingerprint
was not emitted, and the discovery corpus needed a causally distinct composition case before a
"two structurally distinct" success could be asserted.  It also records operator-space nomination
and winning-participation evidence required by the preregistration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re

from experiments import entropygraph_v030_reversible_structure_compiler_o01 as O

SCHEMA = "cmpct-v030-foundry-f01-o01-v2"


def _family(motif: str) -> str:
    if motif.startswith("DIRECT"):
        return "DIRECT"
    if motif.startswith("LANE"):
        return "LANE"
    if motif.startswith("DELIM"):
        return "DELIM"
    if motif.startswith("SPLIT"):
        return "SPLIT"
    if motif.startswith("LITERAL"):
        return "LITERAL"
    return "OTHER"


def _signature(motif: str) -> str:
    # Structural signature deliberately erases parameter values/benchmark identity while retaining
    # the operator composition that caused a win.
    return re.sub(r"\[\d+\]", "[*]", motif.replace("@grid", ""))


def _corpus_fingerprint(cases: list[tuple[str, bytes]]) -> tuple[str, list[dict]]:
    manifest = [
        {"case": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        for name, raw in cases
    ]
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest(), manifest


def run(seed: str) -> dict:
    original_discovery = O._discovery_cases
    original_alternatives = O._alternatives
    nominations: dict[str, int] = {"DIRECT": 0, "LANE": 0, "DELIM": 0, "SPLIT": 0}

    def decisive_discovery() -> list[tuple[str, bytes]]:
        cases = list(original_discovery())
        # Causally distinct from lane+record composition: two adjacent byte-geometries require
        # different fixed-width lane transforms.  The split remains a generic 4 KiB-grid decision.
        left = O._lane_block(8192, 8, 73)[:49152]
        right = O._lane_block(4096, 16, 91)[:49152]
        cases.append(("discovery_mixed_lane_widths", left + right))
        return cases

    def traced_alternatives(raw: bytes, stats: dict[str, int]):
        candidates = original_alternatives(raw, stats)
        for candidate in candidates:
            family = _family(candidate.motif)
            nominations[family] = nominations.get(family, 0) + 1
        return candidates

    # Freeze the corrected discovery corpus and tracing before any result is observed.
    O._discovery_cases = decisive_discovery
    O._alternatives = traced_alternatives
    discovery = decisive_discovery()
    hostile = O._hostile_cases()
    fingerprint, manifest = _corpus_fingerprint(discovery + hostile)
    try:
        result = O.run(seed)
    finally:
        O._discovery_cases = original_discovery
        O._alternatives = original_alternatives

    result["schema"] = SCHEMA
    result["corpus_fingerprint"] = fingerprint
    result["corpus_manifest"] = manifest

    winning_participation = {key: 0 for key in nominations}
    structural_families: dict[str, list[str]] = {key: [] for key in nominations}
    split_ablation_saving = 0
    material_discovery_signatures: set[str] = set()
    for case in result["cases"]:
        motif = case["synthesized_motif"]
        present = {"SPLIT"} if motif.startswith("SPLIT") else set()
        for family in ("DIRECT", "LANE", "DELIM"):
            if family in motif:
                present.add(family)
        for family in present:
            winning_participation[family] = winning_participation.get(family, 0) + 1
            structural_families.setdefault(family, []).append(case["case"])
        # Search evaluates exactly one additive SPLIT candidate per frozen-grid offset after
        # independently minimizing each child.  Count every such nomination, not only winners.
        nominations["SPLIT"] += int(case["search"]["split_points"])
        if motif.startswith("SPLIT"):
            split_ablation_saving += max(0, case["manual_bytes"] - case["synthesized_bytes"])
        if case["role"] == "discovery" and case["material_composed_win"]:
            material_discovery_signatures.add(_signature(motif))

    result["operator_space"] = {
        family: {
            "nomination_count": int(nominations.get(family, 0)),
            "winning_program_participation": int(winning_participation.get(family, 0)),
            "structural_families": sorted(set(structural_families.get(family, []))),
            "net_bytes_under_ablation": split_ablation_saving if family == "SPLIT" else None,
            "ablation_note": (
                "sum of manual-control minus synthesized bytes on split winners"
                if family == "SPLIT" else
                "not isolated in O0.1; parameter/operator ablation is deferred unless the family survives"
            ),
            "redundancy_status": "unknown-until-causal-ablation",
        }
        for family in sorted(nominations)
    }
    result["material_discovery_structural_signatures"] = sorted(material_discovery_signatures)

    # The original small oracle counts material wins but cannot itself prove causal diversity.  Never
    # allow an ADVANCE/DISCOVER decision unless at least two normalized composition signatures survived.
    if result["decision"] in {"ADVANCE_COMPOSITION", "DISCOVER_PRIMITIVE"} and len(material_discovery_signatures) < 2:
        result["decision"] = "SEARCH_INCONCLUSIVE"
        result["strongest_surviving_objection"] = (
            "Material composition headroom was observed, but fewer than two causally distinct normalized "
            "composition signatures survived; the preregistered success witness is therefore incomplete."
        )
        result["next_decisive_test"] = (
            "Rerun the identical frozen grammar/search only after a specific corpus/instrument review; do not add operators."
        )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default=os.environ.get("EVIDENCE_HEAD", ""))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.seed or len(args.seed) < 12:
        raise SystemExit("F-01 O0.1 decisive oracle requires a post-freeze public commit seed")
    result = run(args.seed)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
