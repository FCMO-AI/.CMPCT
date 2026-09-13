from __future__ import annotations

"""H-EFFORT-3: preregistered one-probe repair of C25EG08's false monotonic stop law.

Scientific question: after the first strictly-worse policy rung, can exactly one
fixed level-9 recovery probe recover useful later compression without paying the
full level-19 oracle everywhere?

The rule is deliberately threshold-free and workload/path blind:
* preserve the current payload and hot-root exclusion from C25EG08;
* replay policy levels 3, 6, 12, 19;
* on the first strictly-worse rung, evaluate level 9 exactly once if level 9 has
  not already been passed;
* if level 9 beats the incumbent, retain it and continue with later original
  policy rungs; otherwise stop;
* if the first worse rung occurs after level 9, stop normally.

This is a research counterfactual only. It cannot receive product/R4 credit.
Office and Analytics are the two primary causal surfaces inherited from H-EFFORT-2.
Transfer is deliberately stronger: every other workload emitted by the frozen
current15 stable substrate is held out. The exact ten-name substrate is asserted
before any compression result is accepted, so future corpus drift cannot silently
change the transfer court. No threshold learned from Office/Analytics is permitted.

Important separation: H-EFFORT-3 changes only codec effort over already-fixed
physical units; it cannot change filesystem-control representation, membership,
pack geometry, locality or decode-unit size. Office/Analytics retain their admitted
implicit-v4 control and strict locality gate. Held-out surfaces retain their exact
explicit filesystem control when implicit-v4 is not semantics-preserving; the same
regular-file profile still produces the physical units under test. Strong verify,
filesystem fidelity and tail recovery remain mandatory. Held-out locality is
measured and reported rather than gifted product credit.
"""

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_adaptive_effort_residual_referee as H2
from benchmarks import v030_current15_stable_corpus as CORPUS
from benchmarks import v030_office_physical_economics_referee as OFFICE
from benchmarks import v030_physical_effort_attribution as H1
from experiments import entropygraph_v030_federated_adaptive_effort_candidate_v8 as EG08

EXPECTED_CURRENT15_NAMES = (
    "01_developer_repository",
    "02_office_workspace",
    "03_media_library",
    "04_analytics_and_database",
    "05_logs_and_telemetry",
    "06_incremental_backups",
    "07_incompressible_and_encrypted_like",
    "08_many_tiny_files",
    "09_ml_artifacts",
    "10_large_mixed_binary",
)
PRIMARY = {"02_office_workspace", "04_analytics_and_database"}
TARGETS = EXPECTED_CURRENT15_NAMES
HELD_OUT = set(TARGETS) - PRIMARY
REPS = 3
EXPECTED_POLICY_GIT_BLOB = H2.EXPECTED_POLICY_GIT_BLOB


def _probe_once(units: list[dict], hot_indices: set[int]) -> tuple[list[tuple[int, bytes]], dict]:
    selected: list[tuple[int, bytes]] = []
    attempts = probes = probe_wins = early_stops = 0
    for row in units:
        pi = int(row["index"])
        best_codec = int(row["codec"])
        best_payload = row["payload"]
        best_size = len(best_payload)
        probe_used = False
        if pi not in hot_indices:
            for level in H2.POLICY_LEVELS:
                attempts += 1
                codec, payload = H1._encode(row["raw"], level)
                size = len(payload)
                if size <= best_size:
                    if size < best_size:
                        best_codec, best_payload, best_size = codec, payload, size
                    continue
                if level < 9 and not probe_used:
                    probe_used = True
                    probes += 1
                    attempts += 1
                    pcodec, ppayload = H1._encode(row["raw"], 9)
                    psize = len(ppayload)
                    if psize < best_size:
                        probe_wins += 1
                        best_codec, best_payload, best_size = pcodec, ppayload, psize
                        continue
                early_stops += 1
                break
        selected.append((best_codec, best_payload))
    return selected, {
        "attempts": attempts,
        "recovery_probes": probes,
        "recovery_probe_wins": probe_wins,
        "early_stops": early_stops,
    }


def _timed_probe(units: list[dict], hot: set[int]):
    first = stats0 = None
    cpus = []
    walls = []
    for _ in range(REPS):
        c0 = time.process_time()
        w0 = time.perf_counter()
        out, stats = _probe_once(units, hot)
        cpus.append(time.process_time() - c0)
        walls.append(time.perf_counter() - w0)
        if first is None:
            first, stats0 = out, stats
        elif any(a[0] != b[0] or a[1] != b[1] for a, b in zip(first, out)):
            raise RuntimeError("recovery-probe policy nondeterministic")
    return first, stats0, statistics.median(cpus), statistics.median(walls)


def _explicit_profile_controls(source: Path, profile: Path) -> tuple[bytes, dict]:
    """Build the same regular-file physical profile without changing FS semantics."""
    v1_raw, regular_sources, stats = OFFICE.FS.capture_filesystem_manifest(
        source,
        max_path_bytes=H2.EG05.MAX_PATH_BYTES,
        max_profile_files=H2.EG05.MAX_PROFILE_FILES,
        max_profile_logical_bytes=H2.EG05.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=H2.EG05.MAX_MANIFEST_ENTRIES,
    )
    profile.mkdir(parents=True, exist_ok=True)
    for src, rel in regular_sources:
        dst = profile.joinpath(*PurePosixPath(rel).parts)
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(src, dst, follow_symlinks=False)
        except OSError:
            shutil.copyfile(src, dst)
    return v1_raw, stats


def _research_verify(label: str, archive: Path, source: Path, v1_raw: bytes) -> dict:
    """Verify selector transfer while exposing, not forgiving, geometry debt."""
    expected_tree = H2.EG05._treehash(source)
    verify = H2.EG05.strong_verify(archive, expected_tree=expected_tree)
    locality = H2.EG05.locality_report(archive)

    with tempfile.TemporaryDirectory(prefix=f"{label}-extract-") as td:
        restored = Path(td) / "restored"
        _, cpu, wall = OFFICE.timed(lambda: H2.EG05.extract(archive, restored))
        fidelity = OFFICE.fidelity_raw(restored) == v1_raw
        if not fidelity:
            raise RuntimeError(f"{label} filesystem fidelity mismatch")

    corrupt = archive.with_name(archive.stem + "-primary-corrupt" + archive.suffix)
    shutil.copyfile(archive, corrupt)
    raw = bytearray(corrupt.read_bytes())
    if len(raw) <= H2.EG05.V25.HDR.size:
        raise RuntimeError("archive too short for recovery mutation")
    raw[H2.EG05.V25.HDR.size] ^= 0x01
    corrupt.write_bytes(raw)
    try:
        recovery = H2.EG05.strong_verify(corrupt, expected_tree=expected_tree)["ok"]
    finally:
        corrupt.unlink(missing_ok=True)
    if not recovery:
        raise RuntimeError(f"{label} tail recovery failed")

    rows = locality.get("members", [])
    amps = sorted(float(r["amplification"]) for r in rows)
    total_logical = sum(int(r["logical_bytes"]) for r in rows)
    total_decoded = sum(int(r["decoded_context_bytes"]) for r in rows)
    return {
        "verify": verify,
        "filesystem_fidelity": fidelity,
        "tail_recovery": recovery,
        "extract_cpu_s": cpu,
        "extract_wall_s": wall,
        "extract_throughput_mib_s": (OFFICE.tree_bytes(source) / (1024 * 1024)) / max(wall, 1e-9),
        "within_release_bounds": bool(locality.get("within_release_bounds")),
        "max_member_read_amplification": float(locality["max_member_read_amplification"]),
        "mean_selective_amplification": total_decoded / max(1, total_logical),
        "max_decode_unit_bytes": int(locality["max_decode_unit_bytes"]),
        "member_count": len(rows),
        "p95_member_amplification": amps[min(len(amps) - 1, int(0.95 * len(amps)))] if amps else 0.0,
    }


def _one(source: Path, item: dict, work: Path) -> dict:
    profile = work / "profile"
    if item["name"] in PRIMARY:
        v1_raw, control_raw, _ = OFFICE.profile_controls(source, profile)
        control_kind = "implicit-v4"
    else:
        v1_raw, _ = _explicit_profile_controls(source, profile)
        control_raw = v1_raw
        control_kind = "explicit-v1"

    base = work / "base.cmpct"
    OFFICE.physical_base(profile, base)
    current = work / "current.cmpct"
    OFFICE.embedded_copy(base, current, control_raw)
    if item["name"] in PRIMARY:
        verify = OFFICE.verify_controlled("h-effort-3", current, source, v1_raw, implicit=True)
        verify["within_release_bounds"] = True
    else:
        verify = _research_verify("h-effort-3-heldout", current, source, v1_raw)
    units, _ = H1._physical_units(base)
    meta, _ = H2.EG05._parse_physical_region(base.read_bytes())
    _, hot = EG08._stream_roles(meta, len(units))
    l1, c1, w1 = H2._run_level(units, 1)
    l19, c19, w19 = H2._run_level(units, 19)
    if any(int(r["codec"]) != int(e[0]) or r["payload"] != e[1] for r, e in zip(units, l1)):
        raise RuntimeError("level1 identity failure")
    old, _, oldcpu, oldwall = H2._run_policy(units, hot)
    new, stats, cpu, wall = _timed_probe(units, hot)
    phys = lambda x: H2._physical_bytes(x)
    p1, p19, pold, pnew = map(phys, (l1, l19, old, new))
    oracle = p1 - p19
    return {
        "name": item["name"],
        "tree_sha256": item["tree_sha256"],
        "filesystem_control": control_kind,
        "verify": verify,
        "pack_count": len(units),
        "hot_pack_count": len(hot),
        "level1_physical_bytes": p1,
        "level19_physical_bytes": p19,
        "historical_physical_bytes": pold,
        "probe_physical_bytes": pnew,
        "oracle_saving_bytes": oracle,
        "historical_recovered_bytes": p1 - pold,
        "probe_recovered_bytes": p1 - pnew,
        "probe_share_of_oracle": ((p1 - pnew) / oracle if oracle > 0 else 1.0),
        "probe_residual_bytes": pnew - p19,
        "historical_cpu_s": oldcpu,
        "historical_wall_s": oldwall,
        "probe_cpu_s": cpu,
        "probe_wall_s": wall,
        "level19_cpu_s": c19,
        "level19_wall_s": w19,
        "probe_vs_l19_cpu_ratio": cpu / max(c19, 1e-12),
        "stats": stats,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("adaptive-effort-recovery-probe.json"))
    args = ap.parse_args()
    blob = H2._policy_blob()
    if blob != EXPECTED_POLICY_GIT_BLOB:
        raise RuntimeError(f"policy source drift {blob}")
    with tempfile.TemporaryDirectory(prefix="cmpct-h-effort-3-") as td:
        root = Path(td)
        corpus = root / "corpus"
        manifest = CORPUS.build(corpus)
        by = {x["name"]: x for x in manifest["corpora"]}
        observed_names = tuple(sorted(by))
        expected_names = tuple(sorted(EXPECTED_CURRENT15_NAMES))
        if observed_names != expected_names:
            raise RuntimeError(
                "current15 substrate drift: "
                f"expected={expected_names!r} observed={observed_names!r}"
            )
        rows = [_one(corpus / name, by[name], root / name) for name in TARGETS]
    primary = [r for r in rows if r["name"] in PRIMARY]
    held = [r for r in rows if r["name"] in HELD_OUT]
    primary_ok = all(r["probe_share_of_oracle"] >= 0.90 for r in primary)
    held_no_regress = all(r["probe_physical_bytes"] <= r["historical_physical_bytes"] for r in held)
    compute_ok = all(r["probe_vs_l19_cpu_ratio"] < 0.90 for r in rows)
    verdict = (
        "RECOVERY_PROBE_TRANSFERS"
        if primary_ok and held_no_regress and compute_ok
        else "RECOVERY_PROBE_NOT_READY"
    )
    out = {
        "schema": "cmpct-v030-adaptive-effort-recovery-probe-v4",
        "status": "selector-transfer research evidence; no release, locality, geometry, filesystem-control, or R4 credit",
        "historical_policy_blob": blob,
        "substrate_names": list(EXPECTED_CURRENT15_NAMES),
        "targets": list(TARGETS),
        "primary": sorted(PRIMARY),
        "held_out": sorted(HELD_OUT),
        "rows": rows,
        "verdict": verdict,
        "gates": {
            "primary_ge_90pct_oracle": primary_ok,
            "heldout_no_density_regression": held_no_regress,
            "all_cpu_lt_90pct_l19": compute_ok,
        },
        "note": (
            "threshold-free one-probe falsifier; exact current15 substrate asserted; all non-primary "
            "workloads held out; selector decisions contain no workload/path identity; primary uses admitted "
            "implicit-v4 while held-outs preserve explicit-v1 filesystem semantics; held-out locality is measured "
            "as pre-existing geometry debt and confers no product credit"
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
