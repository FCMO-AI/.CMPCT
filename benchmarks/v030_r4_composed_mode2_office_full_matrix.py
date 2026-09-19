from __future__ import annotations

"""15-workload composition falsifier for two independently positive R4 mechanisms.

This diagnostic composes, without post-hoc best-of selection:
  * Analytics exact dual-owner + existing r24 mode-2 inverse view; and
  * exact duplicate compressed-stream federation for ZIP-like Office containers.

Admission remains structural. Analytics must satisfy the existing exact dual-owner predicate. Otherwise
Office federation is admitted only when the source tree contains byte-identical compressed member
streams shared by at least two ZIP-like containers. Every other workload must fall back byte-identically
to ordinary v0.30. The diagnostic deliberately does not rehabilitate the known mode-2 NPZ locality debt
and does not claim the Office ideal pool-touch model as physical I/O.
"""

import argparse
import json
import os
from pathlib import Path

from benchmarks import v030_r4_dual_owner_full_matrix as MATRIX
from benchmarks import v030_r4_npz_mode2_owner_inversion as MODE2
from benchmarks import v030_r4_office_exact_stream_federation_v2 as OFFICE

SCHEMA = "cmpct-v030-r4-composed-mode2-office-full-matrix-v1"
_ORIGINAL_ADMISSIBLE = MATRIX._dual_admissible
_ADMISSION_KIND: dict[str, str] = {}


def _key(root: Path) -> str:
    return str(root.resolve())


def _combined_admissible(root: Path) -> tuple[bool, dict]:
    dual, discovery = _ORIGINAL_ADMISSIBLE(root)
    if dual:
        _ADMISSION_KIND[_key(root)] = "analytics-mode2"
        return True, {"kind": "analytics-mode2", "dual": discovery}

    containers, shared = OFFICE.discover(root)
    if shared:
        _ADMISSION_KIND[_key(root)] = "office-exact-stream-federation-v2"
        return True, {
            "kind": "office-exact-stream-federation-v2",
            "zip_container_count": len(containers),
            "shared_stream_count": len(shared),
            "shared_stream_bytes": sum(len(v) for v in shared.values()),
        }

    _ADMISSION_KIND[_key(root)] = "ordinary-v030-fallback"
    return False, {
        "kind": "ordinary-v030-fallback",
        "dual": discovery,
        "zip_container_count": len(containers),
        "shared_stream_count": 0,
    }


def _build(root: Path, out: Path, work: Path) -> dict:
    kind = _ADMISSION_KIND.get(_key(root))
    if kind is None:
        admitted, _ = _combined_admissible(root)
        if not admitted:
            raise RuntimeError("combined builder called for non-admitted tree")
        kind = _ADMISSION_KIND[_key(root)]

    if kind == "analytics-mode2":
        d = dict(MODE2._build(root, out, work))
    elif kind == "office-exact-stream-federation-v2":
        d = dict(OFFICE.build_candidate(root, out, work))
    else:
        raise RuntimeError(f"unexpected admitted kind: {kind}")
    d["research_mechanism"] = kind
    return d


def _extract(bundle: Path, out: Path) -> dict:
    if (bundle / "streams.bin").exists() and (bundle / "literal.bin").exists():
        return OFFICE.extract_candidate(bundle, out)
    return MODE2._extract(bundle, out)


# Patch the matrix in both parent and fresh worker processes. Binding __file__ is essential: MATRIX.run
# launches this wrapper as the worker entrypoint so the same composition semantics apply in children.
MATRIX._dual_admissible = _combined_admissible
MATRIX.DUAL._build_candidate = _build
MATRIX.DUAL._extract_candidate = _extract
MATRIX.__file__ = __file__


def run(work: Path) -> dict:
    d = MATRIX.run(work)
    rows = d["rows"]
    admitted = [r for r in rows if r["candidate"]["mode"] == "dual-owner"]
    mechanisms = [r["candidate"].get("research_mechanism") for r in admitted]
    office = next(r for r in rows if r["suite"] == "neutral_hostile_v1" and r["name"] == "02_office_workspace")
    analytics = next(r for r in rows if r["suite"] == "neutral_hostile_v1" and r["name"] == "04_analytics_and_database")
    regressions = [r for r in rows if r["saving_bytes"] < 0]

    h = {
        "exactly_two_structural_admissions": len(admitted) == 2,
        "analytics_admitted_as_mode2": analytics["candidate"].get("research_mechanism") == "analytics-mode2",
        "office_admitted_as_exact_stream_federation": office["candidate"].get("research_mechanism") == "office-exact-stream-federation-v2",
        "zero_byte_regressions": not regressions,
        "analytics_saves_bytes": analytics["saving_bytes"] > 0,
        "office_saves_bytes": office["saving_bytes"] > 0,
        "aggregate_smaller_than_same_run_v030": d["aggregate"]["candidate_bytes"] < d["aggregate"]["baseline_v030_bytes"],
        "candidate_beats_genesis_v029_aggregate": d["aggregate"]["candidate_bytes"] < d["aggregate"]["genesis_v029_bytes"],
    }
    h["supported_for_next_hardening"] = all(h[k] for k in (
        "exactly_two_structural_admissions",
        "analytics_admitted_as_mode2",
        "office_admitted_as_exact_stream_federation",
        "zero_byte_regressions",
        "analytics_saves_bytes",
        "office_saves_bytes",
        "aggregate_smaller_than_same_run_v030",
    ))

    d["schema"] = SCHEMA
    d["source_commit"] = os.environ.get("EVIDENCE_HEAD")
    d["admitted"] = [
        {"suite": r["suite"], "name": r["name"], "mechanism": r["candidate"].get("research_mechanism")}
        for r in admitted
    ]
    d["regressions"] = [
        {"suite": r["suite"], "name": r["name"], "saving_bytes": r["saving_bytes"]}
        for r in regressions
    ]
    d["office"] = {
        "baseline_v030_bytes": office["baseline"]["stored_bytes"],
        "candidate_bytes": office["candidate"]["stored_bytes"],
        "saving_vs_v030_bytes": office["saving_bytes"],
        "create_tree_cpu_delta_s": office["create_tree_cpu_delta_s"],
        "create_wall_delta_s": office["create_wall_delta_s"],
    }
    d["analytics"] = {
        "baseline_v030_bytes": analytics["baseline"]["stored_bytes"],
        "candidate_bytes": analytics["candidate"]["stored_bytes"],
        "accepted_v029_bytes": MATRIX.ACCEPTED_V029_ANALYTICS,
        "saving_vs_v030_bytes": analytics["saving_bytes"],
        "margin_vs_v029_bytes": MATRIX.ACCEPTED_V029_ANALYTICS - analytics["candidate"]["stored_bytes"],
        "create_tree_cpu_delta_s": analytics["create_tree_cpu_delta_s"],
        "create_wall_delta_s": analytics["create_wall_delta_s"],
    }
    d["hypothesis"] = h
    d["contract"] = {
        "diagnostic_only": True,
        "release_credit": False,
        "full_15_workload_matrix": True,
        "same_semantic_tree_verified": True,
        "exact_fallback_required": True,
        "structural_admission_no_workload_name_gate": True,
        "no_posthoc_best_of_selection": True,
        "existing_mode2_semantics_only": True,
        "office_exact_compressed_stream_identity_only": True,
        "mode2_npz_locality_debt_preserved": True,
        "office_pool_touch_is_ideal_not_physical_io": True,
        "no_threshold_sweep": True,
        "rss_is_max_observed_process_not_simultaneous_tree_peak": True,
    }
    d["composition_note"] = {
        "mechanisms": mechanisms,
        "admission_scan_note": "diagnostic composition has not yet fused the Office duplicate-stream scan with ordinary v0.30 observation",
    }
    d["next_if_supported"] = (
        "do not promote yet: rehabilitate mode2 NPZ locality under the preserved density margin and measure actual file-backed Office range I/O; "
        "then rerun the composed matrix with physical selective-access and recovery accounting"
    )
    d["next_if_falsified"] = (
        "preserve the independently positive single-mechanism receipts and attribute composition failure without tuning Genesis thresholds"
    )
    return d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-composed-matrix-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-composed-matrix.json"))
    p.add_argument("--worker", choices=["baseline", "candidate"])
    p.add_argument("--source", type=Path)
    p.add_argument("--archive", type=Path)
    p.add_argument("--worker-result", type=Path)
    a = p.parse_args()
    if a.worker:
        if not (a.source and a.archive and a.worker_result):
            raise SystemExit("worker mode requires --source --archive --worker-result")
        MATRIX._worker(a.worker, a.source, a.archive, a.work_root, a.worker_result)
        return
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps({
        "aggregate": d["aggregate"], "office": d["office"], "analytics": d["analytics"],
        "admitted": d["admitted"], "regressions": d["regressions"], "hypothesis": d["hypothesis"],
    }, indent=2))


if __name__ == "__main__":
    main()
