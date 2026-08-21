from __future__ import annotations

"""Focused shipping regression proof for v0.30's r24 medium-binary S_PACK policy.

The r24-v4 release encoder already admits <=256 KiB ``.bin`` members to the mature revision-24 ``S_PACK``
grammar. Before promotion this file was the A/B oracle. After promotion, comparing the candidate with the current
shipping baseline naturally converges to identical bytes; the useful contract is now different: retain exact-tree
verification and preserve the strict size + complete-create wins against ZIP/Deflate-9 and solid tar+Zstd-19 on
the two hostile families that justified the policy, while never regressing the encrypted-like negative control.

The separate ``v030_r24_medium_binary_pack_generalization.py`` lane owns the historical r24-v3 -> r24-v4
15-workload zero-byte-regression proof. This focused lane cannot authorize release or weaken any external gate.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import neutral_hostile_corpus_v1 as NEUTRAL
from benchmarks import neutral_hostile_determinism_repair_v6 as REPAIR
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_release_product as P

MEDIUM_MAX = 256 * 1024
TARGETS = (
    ("resemblance_hostile_v1/02_false_neighbors", "hostile", "02_false_neighbors", True),
    ("resemblance_hostile_v1/05_incompressible", "hostile", "05_incompressible", True),
    ("neutral_hostile_v1/07_incompressible_and_encrypted_like", "neutral", "07_incompressible_and_encrypted_like", False),
)


def _verified_shipping_r24(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    stats = P._locality_bounded_r24_build(root, out)
    build_s = time.perf_counter() - started
    started = time.perf_counter()
    verified = P.strong_verify(out)
    verify_s = time.perf_counter() - started
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"r24 strong verification failed: {verified!r}")
    if int(stats["micro_pack_max_file_release_bytes"]) != MEDIUM_MAX:
        raise RuntimeError(f"shipping r24 medium-pack ceiling drifted: {stats!r}")
    if stats.get("release_byte_knobs") != "environment-independent-r24-v4":
        raise RuntimeError(f"shipping r24 policy marker drifted: {stats!r}")
    return {
        "archive_bytes": out.stat().st_size,
        "build_s": build_s,
        "verify_s": verify_s,
        "complete_create_s": build_s + verify_s,
        "tree_sha256": verified.get("tree_sha256"),
        "micro_pack_max_file_bytes": int(stats["micro_pack_max_file_release_bytes"]),
        "micro_pack_target_bytes": int(stats["micro_pack_target_release_bytes"]),
        "release_byte_knobs": stats.get("release_byte_knobs"),
    }


def _comparators(root: Path, work: Path) -> dict:
    z = EXT._zip(root, work / "cmp.zip", work / "zip-out")
    s = EXT._tar_zstd(root, work / "cmp.tar.zst", work / "zstd-out", work)
    return {"zip_deflate9": z, "tar_zstd19_solid": s}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral_root = work_root / "neutral"
    hostile_root = work_root / "hostile"
    REPAIR.install_generation_hooks(NEUTRAL)
    NEUTRAL.build(neutral_root)
    REPAIR.normalize_root(neutral_root)
    HOSTILE.build(hostile_root)

    rows = []
    for label, suite, name, positive in TARGETS:
        source = (neutral_root if suite == "neutral" else hostile_root) / name
        with tempfile.TemporaryDirectory(prefix="cmpct-v030-r24-medium-pack-regression-", dir=work_root) as td:
            w = Path(td)
            first = _verified_shipping_r24(source, w / "first.cmpct")
            second = _verified_shipping_r24(source, w / "second.cmpct")
            comps = _comparators(source, w)
        deterministic_bytes = first["archive_bytes"] == second["archive_bytes"]
        same_tree = first["tree_sha256"] == second["tree_sha256"]
        beats_zip_size = first["archive_bytes"] < comps["zip_deflate9"]["archive_bytes"]
        beats_zstd_size = first["archive_bytes"] < comps["tar_zstd19_solid"]["archive_bytes"]
        beats_zip_create = first["complete_create_s"] < comps["zip_deflate9"]["create_s"]
        beats_zstd_create = first["complete_create_s"] < comps["tar_zstd19_solid"]["create_s"]
        strict_four_way = beats_zip_size and beats_zstd_size and beats_zip_create and beats_zstd_create
        rows.append({
            "label": label,
            "positive_target": positive,
            "shipping_r24": first,
            "repeat_r24": second,
            "comparators": comps,
            "deterministic_archive_bytes": deterministic_bytes,
            "same_verified_tree": same_tree,
            "beats_zip_size": beats_zip_size,
            "beats_zstd19_size": beats_zstd_size,
            "beats_zip_create": beats_zip_create,
            "beats_zstd19_create": beats_zstd_create,
            "strict_four_way_win": strict_four_way,
        })
        print(json.dumps({"label": label, "bytes": first["archive_bytes"], "four_way": strict_four_way}, separators=(",", ":")), flush=True)

    positives = [r for r in rows if r["positive_target"]]
    controls = [r for r in rows if not r["positive_target"]]
    gate = {
        "all_verified_tree_equal": all(r["same_verified_tree"] for r in rows),
        "all_archive_bytes_deterministic": all(r["deterministic_archive_bytes"] for r in rows),
        "positive_rows_strict_four_way": all(r["strict_four_way_win"] for r in positives),
        # The negative control is intentionally allowed to remain a Zstd size loss; this lane only proves that
        # r24-v4 itself stays deterministic and verified there. The all-15 external frontier remains authoritative.
        "negative_controls_verified_and_deterministic": all(r["same_verified_tree"] and r["deterministic_archive_bytes"] for r in controls),
    }
    gate["shipping_regression_passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-r24-medium-binary-pack-regression-v2",
        "contract": {
            "grammar": "existing canonical r24 S_PACK only",
            "shipping_micro_pack_max_file_bytes": MEDIUM_MAX,
            "shipping_extra_pack_hint": ".bin",
            "locality_policy": "shipping r24 micro_pack_target remains min(2 MiB, 8x largest regular member)",
            "claim_boundary": "focused shipping regression; historical v3->v4 byte delta belongs to all-15 generalization evidence",
        },
        "rows": rows,
        "gate": gate,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-medium-pack-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-medium-pack.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["gate"], indent=2), flush=True)
    if not result["gate"]["shipping_regression_passed"]:
        raise SystemExit("shipping r24 medium binary pack regression failed")


if __name__ == "__main__":
    main()
