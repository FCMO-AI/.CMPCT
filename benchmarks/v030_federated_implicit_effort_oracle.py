from __future__ import annotations

"""Selective-effort frontier for C25EG03 implicit regular-path ownership.

C25EG02 left office only a few hundred bytes above the immutable v0.29 floor even under the all-best measured pack
bound.  C25EG03 removes duplicate regular path strings from filesystem control while preserving exact canonical
filesystem semantics and using the authenticated federated graph as their sole path/identity owner.

This front door reuses the audited effort/comparator methodology unchanged.  It is research evidence only.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_federated_selective_effort_oracle as V1
from benchmarks import v030_federated_selective_effort_oracle_v4 as V4
from experiments import entropygraph_v030_federated_implicit_candidate as EG03


def _implicit_prepare(source: Path, parent: Path):
    profile = parent / "profile"
    fs = EG03._prepare_profile(source, profile)
    return profile, fs


def run(work_root: Path) -> dict:
    old_candidate = V1.CAND
    old_prepare = V1._prepare
    V1.CAND = EG03
    V1._prepare = _implicit_prepare
    try:
        result = dict(V4.run(work_root))
    finally:
        V1.CAND = old_candidate
        V1._prepare = old_prepare
    result["schema"] = "cmpct-v030-federated-eg03-implicit-effort-v1"
    result["candidate_identity"] = {
        "magic_ascii": EG03.MAGIC.decode("ascii", errors="strict").rstrip("\x00"),
        "profile": "federated-eg03-implicit-fs",
        "regular_path_and_content_identity_owner": "authenticated federated content graph",
        "filesystem_control_owner": "implicit regular-path filesystem manifest v3",
        "patched_candidate_restored": V1.CAND is old_candidate,
        "patched_prepare_restored": V1._prepare is old_prepare,
    }
    result["claim_boundary"] = (
        "research-only C25EG03 ownership frontier. No shipping selector, accepted-v0.29 byte, ZIP/Zstd comparator, "
        "locality/decode ceiling, native/Android support or release authority is changed."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg03-implicit-effort-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg03-implicit-effort.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "measurement_gate": result["measurement_gate"], "candidate_identity": result["candidate_identity"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("implicit federated selective-effort measurement invalid")


if __name__ == "__main__":
    main()
