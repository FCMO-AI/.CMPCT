from __future__ import annotations

"""Exact-byte profiler for the historical Office C25EG08 graph/build boundary.

The current Office candidate is already a strict size win against accepted v0.29, ZIP and
Zstd-19, but its verified creation time still loses to ZIP by roughly the same amount as
``graph_s``.  That label spans several independent historical operations, so changing it
blindly risks spending release time on a small sub-phase.

This oracle runs the real frozen Office stage through the unchanged RAM-backed EG07
semantic builder twice: one ordinary timing pass and one cProfile pass.  The two raw-final
EG07 envelopes must be byte-identical.  Profile time is diagnostic only and receives no
benchmark/release credit; the ordinary pass remains the wall-clock reference.
"""

import argparse
import cProfile
import hashlib
import json
from pathlib import Path
import pstats
import shutil
import tempfile

from benchmarks import v030_federated_compact_framing_v8_policy_distill as OFFICE
from benchmarks import v030_federated_compact_framing_v8_direct_v5 as DIRECT


def _rows(profile: cProfile.Profile, limit: int = 40) -> list[dict]:
    stats = pstats.Stats(profile)
    rows = []
    for (filename, line, function), (primitive_calls, total_calls, self_s, cumulative_s, _callers) in stats.stats.items():
        rows.append(
            {
                "file": str(filename),
                "line": int(line),
                "function": str(function),
                "primitive_calls": int(primitive_calls),
                "total_calls": int(total_calls),
                "self_s": float(self_s),
                "cumulative_s": float(cumulative_s),
            }
        )
    rows.sort(key=lambda row: (-row["cumulative_s"], -row["self_s"], row["file"], row["line"], row["function"]))
    return rows[:limit]


def _owner(row: dict) -> str:
    file = row["file"].replace("\\", "/")
    fn = row["function"]
    if file.endswith("entropygraph_v025.py"):
        if fn == "zc":
            return "zstd_probe_or_pack_compression"
        if fn == "H":
            return "sha256_identity"
        if fn == "build":
            return "historical_build_total"
        return "entropygraph_v025_other"
    if file.endswith("zipfile.py"):
        return "zip_container_parse_or_inflate"
    if "hashlib" in file or fn in {"openssl_sha256", "sha256"}:
        return "sha256_identity"
    if "pathlib" in file or fn in {"read_bytes", "write_bytes", "open"}:
        return "filesystem_or_path"
    if "zstandard" in file or "zstd" in file.lower():
        return "zstd_probe_or_pack_compression"
    return "other"


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, _accepted_v029 = OFFICE._frozen_office(work_root)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-office-profile-", dir=work_root) as td:
        root = Path(td)
        stage = OFFICE.EXT._normalized_stage(source, root / "normalized")

        ordinary_blob, ordinary_s = DIRECT._tmpfs_capture_raw_final_eg07(stage, root / "ordinary")
        profiler = cProfile.Profile()
        profiler.enable()
        profiled_blob, profiled_wall_s = DIRECT._tmpfs_capture_raw_final_eg07(stage, root / "profiled")
        profiler.disable()

    if ordinary_blob != profiled_blob:
        raise RuntimeError("Office graph profiling changed raw-final EG07 bytes")

    top = _rows(profiler)
    owners: dict[str, dict[str, float | int]] = {}
    # Self time is additive across functions; use it for owner totals. Cumulative time is
    # retained per function above for call-tree diagnosis but must not be summed.
    for row in top:
        owner = _owner(row)
        item = owners.setdefault(owner, {"self_s": 0.0, "functions_in_top": 0})
        item["self_s"] = float(item["self_s"]) + float(row["self_s"])
        item["functions_in_top"] = int(item["functions_in_top"]) + 1

    return {
        "schema": "cmpct-v030-office-graph-hotpath-profile-v1",
        "archive_bytes": len(ordinary_blob),
        "archive_sha256": hashlib.sha256(ordinary_blob).hexdigest(),
        "exact_raw_final_identity": True,
        "ordinary_graph_wall_s": float(ordinary_s),
        "profiled_graph_wall_s": float(profiled_wall_s),
        "profile_timing_release_credit": False,
        "top_functions_by_cumulative_s": top,
        "top_function_self_time_by_owner": owners,
        "contract": {
            "frozen_office_source": True,
            "historical_graph_semantics_changed": False,
            "raw_final_eg07_byte_identity_required": True,
            "profile_numbers_are_diagnostic_only": True,
            "release_credit": False,
        },
        "claim_boundary": (
            "Diagnostic-only exact-byte hotpath evidence for the historical Office graph/build boundary. "
            "It changes no encoder, selector, grammar, integrity, recovery or locality behavior and grants "
            "no release credit. Any optimization suggested by this profile must independently prove exact "
            "final C25EG08 identity and the frozen external/runtime contracts before promotion."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-office-graph-profile-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-office-graph-profile.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "archive_bytes": result["archive_bytes"],
        "ordinary_graph_wall_s": result["ordinary_graph_wall_s"],
        "profiled_graph_wall_s": result["profiled_graph_wall_s"],
        "top_function_self_time_by_owner": result["top_function_self_time_by_owner"],
        "top_functions_by_cumulative_s": result["top_functions_by_cumulative_s"][:15],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
