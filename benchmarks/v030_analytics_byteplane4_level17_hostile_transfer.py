from __future__ import annotations

"""Generator-distinct hostile transfer for the fixed BytePlane4 + level-17 seed.

Mission: docs/V030_ANALYTICS_BYTEPLANE4_LEVEL17_HOSTILE_TRANSFER_MISSION_2026-09-12.md
Research-only. Width/level/gate are frozen from the positive Analytics seed.
"""

import argparse
import json
from pathlib import Path
import random
import shutil
import statistics
import struct
import zlib

from benchmarks import v030_analytics_byteplane4_strong_transfer_referee as BP
from experiments import entropygraph_v030_release_product as PRODUCT

LEVEL17 = 17
LEVEL19 = 19
WIDTH = 4
ROUNDS = 2
FILE_COUNT = 8
FILE_BYTES = 256 * 1024
MIN_POSITIVE_SPEEDUP_VS_L19 = 0.20


def _write_chunks(root: Path, payload: bytes, suffix: str = ".dat") -> None:
    root.mkdir(parents=True, exist_ok=True)
    if len(payload) != FILE_COUNT * FILE_BYTES:
        raise RuntimeError("fixture payload size drift")
    for i in range(FILE_COUNT):
        b = payload[i * FILE_BYTES : (i + 1) * FILE_BYTES]
        (root / f"f{i:02d}{suffix}").write_bytes(b)


def _counter32(n: int) -> bytes:
    out = bytearray(n)
    words = n // 4
    for i in range(words):
        # Nonlinear offset avoids a toy all-zero high plane while preserving real byte-position structure.
        v = (i * 2654435761 + ((i >> 7) * 97)) & 0xFFFFFFFF
        struct.pack_into("<I", out, i * 4, v)
    return bytes(out)


def _mixed32(n: int) -> bytes:
    out = bytearray(n)
    words = n // 4
    for i in range(words):
        o = i * 4
        out[o] = (i * 73 + (i >> 5)) & 0xFF
        out[o + 1] = (i // 17) & 0x0F
        out[o + 2] = (i // 4096) & 0xFF
        out[o + 3] = 1 if (i // 131072) & 1 else 0
    return bytes(out)


def _random32(n: int, seed: int = 0xC0A30) -> bytes:
    return random.Random(seed).randbytes(n)


def _precompressed(n: int) -> bytes:
    # Equal-size outer fixture assembled from independent zlib frames over deterministic random bytes.
    rng = random.Random(0xB17E)
    out = bytearray()
    chunk = 64 * 1024
    while len(out) < n:
        src = rng.randbytes(chunk)
        out += zlib.compress(src, 6)
    return bytes(out[:n])


def _fixtures(root: Path) -> dict[str, dict]:
    total = FILE_COUNT * FILE_BYTES
    defs = {
        "counter32": {"kind": "positive", "bytes": _counter32(total)},
        "mixed32": {"kind": "positive", "bytes": _mixed32(total)},
        "random32": {"kind": "negative", "bytes": _random32(total)},
        "precompressed": {"kind": "negative", "bytes": _precompressed(total)},
    }
    result = {}
    for name, d in defs.items():
        p = root / name
        _write_chunks(p, d["bytes"])
        result[name] = {"kind": d["kind"], "root": p, "tree": PRODUCT.treehash(p)}
    return result


def _build_at(stage: Path, out: Path, *, level: int, candidate: bool) -> dict:
    old_level = BP.LEVEL
    try:
        BP.LEVEL = int(level)
        return BP._build(stage, out, "candidate" if candidate else "baseline")
    finally:
        BP.LEVEL = old_level


def _summarize(rows: list[dict]) -> dict:
    sizes = {int(r["archive_bytes"]) for r in rows}
    trees = {r["canonical_user_tree_sha256"] for r in rows}
    if len(sizes) != 1 or len(trees) != 1:
        raise RuntimeError("mode nondeterminism")
    return {
        "archive_bytes": next(iter(sizes)),
        "median_complete_verified_create_s": statistics.median(float(r["complete_verified_create_s"]) for r in rows),
        "median_process_cpu_s": statistics.median(float(r["process_cpu_s"]) for r in rows),
        "median_process_wall_s": statistics.median(float(r["process_wall_s"]) for r in rows),
        "median_peak_rss_kib": statistics.median(int(r["rss_peak_kib"]) for r in rows),
    }


def run(work_root: Path) -> dict:
    if BP.WIDTH != WIDTH:
        raise RuntimeError("frozen width drift")
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    fixtures = _fixtures(work_root / "fixtures")
    output = {}

    specs = {
        "direct_l17": (LEVEL17, False),
        "bp4_l17": (LEVEL17, True),
        "direct_l19": (LEVEL19, False),
    }

    for fi, (name, fixture) in enumerate(fixtures.items()):
        rows = {k: [] for k in specs}
        names = list(specs)
        for ri in range(ROUNDS):
            order = names[(ri + fi) % len(names):] + names[: (ri + fi) % len(names)]
            for mode in order:
                level, candidate = specs[mode]
                out = work_root / "rounds" / name / f"r{ri}-{mode}"
                out.mkdir(parents=True, exist_ok=True)
                r = _build_at(fixture["root"], out, level=level, candidate=candidate)
                if r["canonical_user_tree_sha256"] != fixture["tree"]:
                    raise RuntimeError(f"tree drift: {name}/{mode}")
                rows[mode].append(r)

        modes = {mode: _summarize(rr) for mode, rr in rows.items()}
        crows = rows["bp4_l17"]
        stat_keys = (
            "cheap_gate_auditions", "cheap_gate_winners", "strong_transform_auditions",
            "strong_transform_selected", "strong_transform_raw_bytes", "net_payload_saving_bytes",
        )
        stable = {}
        for key in stat_keys:
            values = {int(r["stats"][key]) for r in crows}
            if len(values) != 1:
                raise RuntimeError(f"candidate stat drift {name}/{key}: {values}")
            stable[key] = next(iter(values))
        stable["median_cheap_gate_cpu_s"] = statistics.median(float(r["stats"]["cheap_gate_cpu_s"]) for r in crows)
        stable["median_strong_transform_cpu_s"] = statistics.median(float(r["stats"]["strong_transform_cpu_s"]) for r in crows)

        cand = modes["bp4_l17"]
        l17 = modes["direct_l17"]
        l19 = modes["direct_l19"]
        speedup = 1.0 - float(cand["median_complete_verified_create_s"]) / max(float(l19["median_complete_verified_create_s"]), 1e-12)
        output[name] = {
            "kind": fixture["kind"],
            "modes": modes,
            "candidate_stats": stable,
            "saving_vs_l17_bytes": int(l17["archive_bytes"]) - int(cand["archive_bytes"]),
            "candidate_minus_l19_bytes": int(cand["archive_bytes"]) - int(l19["archive_bytes"]),
            "speedup_vs_l19_fraction": speedup,
        }

    positive_gates = {}
    negative_gates = {}
    for name, row in output.items():
        if row["kind"] == "positive":
            positive_gates[name] = {
                "selected_transform": row["candidate_stats"]["strong_transform_selected"] >= 1,
                "candidate_smaller_than_l17": row["saving_vs_l17_bytes"] > 0,
                "speedup_vs_l19_at_least_20pct": row["speedup_vs_l19_fraction"] >= MIN_POSITIVE_SPEEDUP_VS_L19,
            }
        else:
            negative_gates[name] = {
                "zero_strong_transform_selection": row["candidate_stats"]["strong_transform_selected"] == 0,
                "candidate_equals_direct_l17": row["modes"]["bp4_l17"]["archive_bytes"] == row["modes"]["direct_l17"]["archive_bytes"],
            }

    gate = {
        "all_positive_transfer_gates": all(all(v.values()) for v in positive_gates.values()),
        "all_negative_rejection_gates": all(all(v.values()) for v in negative_gates.values()),
        "exact_tree_all_modes": True,
        "fixed_level17_width4_no_sweep": True,
    }
    verdict = "LEVEL17_BP4_GENERATOR_TRANSFER" if all(gate.values()) else "RETIRE_BP4_L17_GENERALIZATION_CLAIM"
    return {
        "schema": "cmpct-v030-analytics-bp4-l17-hostile-transfer-v1",
        "experiment_valid": True,
        "release_credit": False,
        "rounds": ROUNDS,
        "fixtures": output,
        "positive_gates": positive_gates,
        "negative_gates": negative_gates,
        "gate": gate,
        "verdict": verdict,
        "contract": {
            "level17_width4_gate_frozen_from_seed": True,
            "generator_distinct": True,
            "path_extension_workload_identity_forbidden": True,
            "no_level_width_threshold_sweep": True,
            "false_friend_selection_is_failure": True,
            "strong_verify_inside_creation_time": True,
            "canonical_format_changed": False,
            "release_credit": False,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-bp4-l17-hostile-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-bp4-l17-hostile.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"verdict": result["verdict"], "fixtures": result["fixtures"], "gate": result["gate"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
