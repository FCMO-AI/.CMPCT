from __future__ import annotations

"""Repeat the exact selective-effort frontier against the structural C25EG02 filesystem candidate.

The C25EG01 effort experiment conclusively showed that office cannot cross accepted v0.29 by compression effort
alone and analytics can do so only with far more CPU than the ZIP creation budget. C25EG02 removes duplicate
regular-file identity from the filesystem control plane, interns repeated metadata, and path-prefixes that control
plane while preserving exact semantics and requiring an exact graph/manifest regular-path match.

This front door deliberately reuses the already-audited selective-effort model, comparator methodology, frozen
accepted-v0.29 schema adapter, levels 1..22, strong verification and locality accounting. Only the candidate
profile preparation/identity is swapped, and all patched module state is restored before returning.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_federated_selective_effort_oracle as V1
from benchmarks import v030_federated_selective_effort_oracle_v4 as V4
from experiments import entropygraph_v030_federated_compact_candidate as EG02


def _compact_prepare(source: Path, parent: Path):
    profile = parent / "profile"
    fs = EG02._prepare_profile(source, profile)
    return profile, fs


def run(work_root: Path) -> dict:
    old_candidate = V1.CAND
    old_prepare = V1._prepare
    V1.CAND = EG02
    V1._prepare = _compact_prepare
    try:
        result = dict(V4.run(work_root))
    finally:
        V1.CAND = old_candidate
        V1._prepare = old_prepare
    result["schema"] = "cmpct-v030-federated-eg02-compact-effort-v1"
    result["candidate_identity"] = {
        "magic_ascii": EG02.MAGIC.decode("ascii", errors="strict").rstrip("\x00"),
        "profile": "federated-eg02-compact-fs",
        "regular_content_identity_owner": "authenticated federated content graph",
        "filesystem_control_owner": "compact authenticated filesystem manifest v2",
        "patched_candidate_restored": V1.CAND is old_candidate,
        "patched_prepare_restored": V1._prepare is old_prepare,
    }
    result["claim_boundary"] = (
        "research-only C25EG02 structural + selective-effort frontier. It changes no shipping selector, accepted-"
        "v0.29 byte, ZIP/Zstd comparator, locality/decode ceiling, native/Android support or release authority. "
        "The experiment asks whether removing duplicate filesystem/content identity changes the previously "
        "falsified effort-only conclusion."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg02-compact-effort-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg02-compact-effort.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "measurement_gate": result["measurement_gate"], "candidate_identity": result["candidate_identity"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("compact federated selective-effort measurement invalid")


if __name__ == "__main__":
    main()
