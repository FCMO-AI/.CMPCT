from __future__ import annotations

"""Fixed-geometry compression-effort oracle for the reactivated v0.30 frontier.

Mission lock: docs/V030_PHYSICAL_EFFORT_ATTRIBUTION_MISSION_LOCK_2026-09-13.md

This benchmark never changes pack membership or materializes the level-19
counterfactual as a product archive. It proves the current level-1 payloads from the
same raw decode units first, then prices stronger compression on those exact units.
"""

import argparse
import binascii
import ctypes
import json
from pathlib import Path
import platform
import resource
import statistics
import tempfile
import time

from benchmarks import v030_current15_stable_corpus as CORPUS
from benchmarks import v030_office_physical_economics_referee as OFFICE
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v5 as EG05

V25 = EG05.V25
TARGETS = ("02_office_workspace", "04_analytics_and_database")
CURRENT_LEVEL = 1
MATURE_LEVEL = 19
REPS = 3


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _zstd_version() -> str:
    try:
        V25.z.ZSTD_versionString.argtypes = []
        V25.z.ZSTD_versionString.restype = ctypes.c_char_p
        raw = V25.z.ZSTD_versionString()
        return (raw or b"unknown").decode(errors="replace")
    except Exception:
        return "unknown"


def _encode(raw: bytes, level: int) -> tuple[int, bytes]:
    comp = V25.zc(raw, int(level))
    if len(comp) + 8 < len(raw):
        return 1, comp
    return 0, raw


def _physical_units(archive: Path) -> tuple[list[dict], dict]:
    meta, physical = EG05._parse_physical_region(archive.read_bytes())
    pos = 0
    rows: list[dict] = []
    for index in range(int(meta["pack_count"])):
        if pos + V25.PH.size > len(physical):
            raise RuntimeError(f"pack {index} header exceeds physical region")
        codec, usize, csize, crc, expected_sha = V25.PH.unpack_from(physical, pos)
        pos += V25.PH.size
        end = pos + int(csize)
        if end > len(physical):
            raise RuntimeError(f"pack {index} payload exceeds physical region")
        payload = physical[pos:end]
        pos = end
        if int(codec) == 0:
            raw = payload
        elif int(codec) == 1:
            raw = V25.zd(payload, int(usize))
        else:
            raise RuntimeError(f"unexpected physical pack codec {codec} at {index}")
        if len(raw) != int(usize):
            raise RuntimeError(f"pack {index} logical length mismatch")
        if (binascii.crc32(raw) & 0xFFFFFFFF) != int(crc):
            raise RuntimeError(f"pack {index} CRC mismatch")
        if V25.H(raw) != expected_sha:
            raise RuntimeError(f"pack {index} SHA mismatch")
        rows.append(
            {
                "index": index,
                "codec": int(codec),
                "usize": int(usize),
                "payload": payload,
                "raw": raw,
                "stored_physical_bytes": V25.PH.size + len(payload),
            }
        )
    if pos != len(physical):
        raise RuntimeError("physical region has trailing bytes")
    return rows, {
        "physical_region_bytes": len(physical),
        "pack_count": len(rows),
        "raw_pack_bytes": sum(len(r["raw"]) for r in rows),
    }


def _run_effort(units: list[dict], level: int) -> tuple[list[tuple[int, bytes]], float, float]:
    cpu_samples: list[float] = []
    wall_samples: list[float] = []
    first: list[tuple[int, bytes]] | None = None
    for _ in range(REPS):
        c0 = time.process_time()
        w0 = time.perf_counter()
        encoded = [_encode(r["raw"], level) for r in units]
        cpu_samples.append(time.process_time() - c0)
        wall_samples.append(time.perf_counter() - w0)
        if first is None:
            first = encoded
        else:
            if len(first) != len(encoded) or any(a[0] != b[0] or a[1] != b[1] for a, b in zip(first, encoded)):
                raise RuntimeError(f"level-{level} compression is not deterministic within run")
    assert first is not None
    return first, statistics.median(cpu_samples), statistics.median(wall_samples)


def _classify(regret: int, recovered: int) -> tuple[str, float]:
    if regret <= 0:
        return "NO_POSITIVE_REGRET", 0.0
    fraction = recovered / regret
    if fraction >= 0.50:
        return "EFFORT_DOMINATES", fraction
    if fraction <= 0.20:
        return "GEOMETRY_DOMINATES", fraction
    return "MIXED", fraction


def _one(source: Path, item: dict, work: Path, frozen_checkout: Path) -> dict:
    profile = work / "profile"
    v1_raw, implicit_raw, fs_stats = OFFICE.profile_controls(source, profile)

    base = work / "physical-base.cmpct"
    base_stats, base_cpu, base_wall = OFFICE.timed(lambda: OFFICE.physical_base(profile, base))
    current = work / "current-implicit.cmpct"
    OFFICE.embedded_copy(base, current, implicit_raw)
    components = OFFICE.parsed(current)
    verify = OFFICE.verify_controlled("effort-current", current, source, v1_raw, implicit=True)
    frozen = OFFICE.frozen_v029(source, work / "v029.cmpct", frozen_checkout)

    units, physical = _physical_units(base)
    level1, l1_cpu, l1_wall = _run_effort(units, CURRENT_LEVEL)
    exact_rows = []
    all_exact = True
    for row, enc in zip(units, level1):
        exact = row["codec"] == enc[0] and row["payload"] == enc[1]
        all_exact = all_exact and exact
        exact_rows.append(
            {
                "index": row["index"],
                "usize": row["usize"],
                "stored_codec": row["codec"],
                "reencoded_codec": enc[0],
                "stored_payload_bytes": len(row["payload"]),
                "reencoded_payload_bytes": len(enc[1]),
                "exact": exact,
            }
        )

    level19, l19_cpu, l19_wall = _run_effort(units, MATURE_LEVEL)
    current_physical = sum(V25.PH.size + len(enc[1]) for enc in level1)
    mature_physical = sum(V25.PH.size + len(enc[1]) for enc in level19)
    if current_physical != int(components["physical_region_bytes"]):
        all_exact = False

    current_total = int(components["archive_bytes"])
    mature_counterfactual_total = current_total - current_physical + mature_physical
    v029_bytes = int(frozen["archive_bytes"])
    regret = current_total - v029_bytes
    recovered = current_total - mature_counterfactual_total
    classification, fraction = _classify(regret, recovered)

    return {
        "name": item["name"],
        "tree_sha256": item["tree_sha256"],
        "logical_bytes": item["logical_bytes"],
        "files": item["files"],
        "frozen_v029": frozen,
        "current_complete_bytes": current_total,
        "current_complete_regret_vs_v029_bytes": regret,
        "current_components": components,
        "current_verify": verify,
        "filesystem_stats": fs_stats,
        "physical_base_build_cpu_s": base_cpu,
        "physical_base_build_wall_s": base_wall,
        "physical_base_stats": base_stats,
        "pack_count": physical["pack_count"],
        "raw_pack_bytes": physical["raw_pack_bytes"],
        "current_physical_bytes": current_physical,
        "mature_effort_physical_bytes": mature_physical,
        "mature_effort_physical_saving_bytes": current_physical - mature_physical,
        "mature_effort_counterfactual_complete_bytes": mature_counterfactual_total,
        "regret_recovered_bytes": recovered,
        "regret_recovered_fraction": fraction,
        "classification": classification,
        "level1_exact_reproduction": all_exact,
        "level1_median_cpu_s": l1_cpu,
        "level1_median_wall_s": l1_wall,
        "level19_median_cpu_s": l19_cpu,
        "level19_median_wall_s": l19_wall,
        "level19_vs_level1_cpu_ratio": l19_cpu / max(l1_cpu, 1e-12),
        "level19_vs_level1_wall_ratio": l19_wall / max(l1_wall, 1e-12),
        "exact_rows": exact_rows,
        "counterfactual_note": "level19 bytes are an oracle on identical raw physical units, not a materialized product archive",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v029-checkout", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("physical-effort-attribution.json"))
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="cmpct-physical-effort-") as td:
        root = Path(td)
        corpus = root / "corpus"
        manifest = CORPUS.build(corpus)
        by_name = {x["name"]: x for x in manifest["corpora"]}
        if any(name not in by_name for name in TARGETS):
            raise RuntimeError("stable current15 target drift")

        rows = []
        for name in TARGETS:
            work = root / ("work-" + name)
            work.mkdir()
            rows.append(_one(corpus / name, by_name[name], work, args.v029_checkout))

        exact = all(r["level1_exact_reproduction"] for r in rows)
        if not exact:
            verdict = "PHYSICAL_EFFORT_ATTRIBUTION_INVALID"
        else:
            office = next(r for r in rows if r["name"] == "02_office_workspace")
            analytics = next(r for r in rows if r["name"] == "04_analytics_and_database")
            if office["classification"] == "EFFORT_DOMINATES" and analytics["classification"] != "GEOMETRY_DOMINATES":
                verdict = "PHYSICAL_EFFORT_DOMINATES"
            elif office["classification"] == "GEOMETRY_DOMINATES" and analytics["classification"] != "EFFORT_DOMINATES":
                verdict = "PHYSICAL_GEOMETRY_DOMINATES"
            else:
                verdict = "PHYSICAL_EFFORT_GEOMETRY_MIXED"

        receipt = {
            "schema": "cmpct-v030-physical-effort-attribution-v1",
            "verdict": verdict,
            "current_level": CURRENT_LEVEL,
            "mature_level": MATURE_LEVEL,
            "repetitions": REPS,
            "zstd_version": _zstd_version(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "process_peak_rss_kib": _rss_kib(),
            "rows": rows,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(receipt, sort_keys=True))
        if verdict == "PHYSICAL_EFFORT_ATTRIBUTION_INVALID":
            raise SystemExit(2)


if __name__ == "__main__":
    main()
