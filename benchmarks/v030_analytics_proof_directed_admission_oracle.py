from __future__ import annotations

"""Path-blind Analytics admission oracle for the v0.30/r25 research frontier.

Mission lock: docs/V030_ANALYTICS_PROOF_DIRECTED_ADMISSION_MISSION_2026-09-12.md

This referee does not change the archive representation or production selector. It measures the
ordinary physical packs already produced by the canonical-filesystem CMPNX5 research mechanism at
fixed effort levels 15 and 19, proves raw-pack identity, computes bounded content-only observables,
and asks whether a cheap admission law can retain the byte-paying packs without paying L19 globally.

Important: diagnostic path/extension labels are deliberately absent from the selector inputs and from
this receipt. Pack SHA is used only to join byte-identical L15/L19 physical packs, never as a feature.
"""

import argparse
import binascii
from collections import Counter
import json
import math
from pathlib import Path
import shutil
import time

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_v025_canonical_fs_level1_oracle as CANON
from experiments import entropygraph_v025 as V25

TARGET = "04_analytics_and_database"
LEVELS = (15, 19)
PREFIX = 4096


def _entropy(sample: bytes) -> float:
    if not sample:
        return 0.0
    counts = Counter(sample)
    n = len(sample)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _observables(raw: bytes, cheap_csize: int) -> dict:
    # Bounded prefix features: O(min(pack, 4 KiB)), independent of path/type/corpus labels.
    s = raw[:PREFIX]
    if not s:
        return {"usize": 0, "cheap_ratio_ppm": 0, "prefix_entropy_milli": 0,
                "prefix_unique": 0, "prefix_run_ppm": 0, "prefix_zero_ppm": 0}
    runs = 1 + sum(a != b for a, b in zip(s, s[1:]))
    return {
        "usize": len(raw),
        "cheap_ratio_ppm": int(1_000_000 * cheap_csize / max(1, len(raw))),
        "prefix_entropy_milli": int(round(1000 * _entropy(s))),
        "prefix_unique": len(set(s)),
        "prefix_run_ppm": int(1_000_000 * runs / len(s)),
        "prefix_zero_ppm": int(1_000_000 * s.count(0) / len(s)),
    }


def _decode_pack(f, entry: tuple) -> bytes:
    """Decode one CMPNX5 physical pack from the authoritative open_ar() pack table.

    Keep this local to the referee instead of inventing a helper on the frozen research engine:
    open_ar() already returns the exact payload offset and authenticated pack metadata used by
    extract().  This mirrors extract()'s pack path while additionally checking the stored SHA-256,
    because cross-level raw-pack identity is the premise of this oracle.
    """
    off, codec, usize, csize, crc, hh = entry
    f.seek(int(off))
    payload = f.read(int(csize))
    if len(payload) != int(csize):
        raise RuntimeError("truncated physical pack payload")
    if int(codec) == 1:
        raw = V25.zd(payload, int(usize))
    elif int(codec) == 0:
        raw = payload
    else:
        raise RuntimeError(f"unsupported physical pack codec {codec}")
    if len(raw) != int(usize):
        raise RuntimeError("physical pack size drift")
    if (binascii.crc32(raw) & 0xFFFFFFFF) != int(crc):
        raise RuntimeError("physical pack CRC drift")
    if V25.H(raw) != bytes(hh):
        raise RuntimeError("physical pack SHA drift")
    return raw


def _build(stage: Path, root: Path, level: int) -> dict:
    old_cap = CANON.LEVEL_CAP
    CANON.LEVEL_CAP = level
    try:
        result = CANON._canonical_v25(stage, root)
    finally:
        CANON.LEVEL_CAP = old_cap

    archive = root / "candidate.cmpnx5"
    V25.OUT = archive
    f, meta, po = V25.open_ar()
    try:
        packs = []
        for pi, entry in enumerate(po):
            _off, codec, usize, csize, crc, hh = entry
            # Decode from the archive itself. This makes feature extraction independent of source paths.
            raw = _decode_pack(f, entry)
            packs.append({
                "pi": int(pi), "codec": int(codec), "usize": int(usize), "csize": int(csize),
                "crc32": int(crc), "sha256": bytes(hh).hex(), "raw": raw,
            })
    finally:
        f.close()
    return {
        "archive_bytes": int(result["archive_bytes"]),
        "complete_verified_create_s": float(result["complete_verified_create_s"]),
        "build_stats": result["build_stats"], "packs": packs,
    }


def _candidate_rules(rows: list[dict]) -> list[dict]:
    # Small mechanism-oriented family, not a dense threshold sweep. Rules are content-only and monotone.
    sizes = (128 * 1024, 256 * 1024, 512 * 1024)
    ratios = (700_000, 850_000, 950_000)
    out = []
    for min_size in sizes:
        for max_ratio in ratios:
            out.append({"min_size": min_size, "max_ratio_ppm": max_ratio})
    return out


def _admits(obs: dict, rule: dict) -> bool:
    return obs["usize"] >= rule["min_size"] and obs["cheap_ratio_ppm"] <= rule["max_ratio_ppm"]


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_analytics_proof_admission_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_analytics_proof_admission_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    stage = EXT._normalized_stage(corpus / TARGET, work_root / "normalized")

    builds = {level: _build(stage, work_root / f"level-{level}", level) for level in LEVELS}
    low, high = builds[15], builds[19]
    lo = {p["sha256"]: p for p in low["packs"]}
    hi = {p["sha256"]: p for p in high["packs"]}
    if set(lo) != set(hi):
        raise RuntimeError("raw physical pack identity drift between fixed L15/L19 controls")

    obs_started = time.perf_counter()
    rows = []
    for hh in sorted(lo):
        a, b = lo[hh], hi[hh]
        if a["usize"] != b["usize"] or a["crc32"] != b["crc32"] or a["raw"] != b["raw"]:
            raise RuntimeError(f"raw pack proof drift for {hh}")
        obs = _observables(a["raw"], a["csize"])
        rows.append({
            "sha256": hh, "l15_csize": a["csize"], "l19_csize": b["csize"],
            "saving_bytes": int(a["csize"] - b["csize"]), "observables": obs,
        })
    observation_s = time.perf_counter() - obs_started

    # Oracle accounting: emitted bytes = fixed L15 archive minus savings of admitted packs.
    # This deliberately excludes runtime claims until an actual selective Builder executes the admitted work.
    rules = []
    true_winners = {r["sha256"] for r in rows if r["saving_bytes"] > 0}
    for rule in _candidate_rules(rows):
        admitted = [r for r in rows if _admits(r["observables"], rule)]
        retained = {r["sha256"] for r in admitted if r["saving_bytes"] > 0}
        saving = sum(r["saving_bytes"] for r in admitted)
        candidate_bytes = int(low["archive_bytes"] - saving)
        rules.append({
            **rule,
            "admitted_packs": len(admitted),
            "true_winners_retained": len(retained),
            "false_negatives": len(true_winners - retained),
            "false_positives": sum(r["saving_bytes"] <= 0 for r in admitted),
            "oracle_saving_bytes": int(saving),
            "oracle_archive_bytes": candidate_bytes,
            "meets_v029_density": candidate_bytes <= 6_135_172,
        })
    # Mechanism-first ranking: density is mandatory, then least expensive admissions, then byte margin.
    viable = [r for r in rules if r["meets_v029_density"]]
    best = min(viable, key=lambda r: (r["admitted_packs"], r["oracle_archive_bytes"])) if viable else min(
        rules, key=lambda r: (r["oracle_archive_bytes"], r["admitted_packs"])
    )

    # Do not serialize raw bytes; receipt contains only content-derived measurements and identity proofs.
    return {
        "schema": "cmpct-v030-analytics-proof-directed-admission-oracle-v1",
        "target": f"neutral_hostile_v1/{TARGET}",
        "release_credit": False,
        "experiment_valid": True,
        "fixed_levels": list(LEVELS),
        "l15_archive_bytes": low["archive_bytes"],
        "l19_archive_bytes": high["archive_bytes"],
        "accepted_v029_bytes": 6_135_172,
        "observation_wall_s": observation_s,
        "pack_count": len(rows),
        "true_paying_packs": len(true_winners),
        "rules": rules,
        "best_rule": best,
        "rows": rows,
        "contract": {
            "same_normalized_source": True,
            "same_raw_pack_identity": True,
            "path_blind_features_only": True,
            "bounded_prefix_bytes": PREFIX,
            "no_format_change": True,
            "no_production_selector_change": True,
            "no_release_credit": True,
            "runtime_claim_requires_selective_builder": True,
        },
        "next_decision": "BUILD_FROZEN_SELECTIVE_ADMISSION" if best["meets_v029_density"] else "ESCALATE_TO_CHEAPER_PROOF_OR_NATIVE",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-analytics-proof-admission-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-analytics-proof-admission.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"best_rule": result["best_rule"], "observation_wall_s": result["observation_wall_s"],
                      "next_decision": result["next_decision"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
