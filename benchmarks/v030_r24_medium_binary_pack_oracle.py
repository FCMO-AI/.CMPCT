from __future__ import annotations

"""Focused shipping regression proof for v0.30's r24 medium-binary S_PACK policy.

The r24-v4 release encoder already admits <=256 KiB ``.bin`` members to the mature revision-24 ``S_PACK``
grammar. Before promotion this file was the A/B oracle. After promotion, comparing the candidate with the current
shipping baseline naturally converges to identical bytes; the useful contract is now different: retain exact-tree
verification and preserve the strict size + complete-create wins against ZIP/Deflate-9 and solid tar+Zstd-19 on
the two hostile families that justified the policy, while never regressing the encrypted-like negative control.

Creation times on these rows are often only a few tenths of a second. A single process/noise sample can therefore
reverse a strict ZIP comparison even when the ordinary external frontier is stable. This ratchet uses repeated,
rotated same-runner measurements and medians while keeping the exact same strict per-format inequalities. Every
CMPCT timing still includes r24 build + mandatory strong verification; no preprocessing or verification cost is
moved outside the measured boundary.

The separate ``v030_r24_medium_binary_pack_generalization.py`` lane owns the historical r24-v3 -> r24-v4
15-workload zero-byte-regression proof. This focused lane cannot authorize release or weaken any external gate.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import neutral_hostile_corpus_v1 as NEUTRAL
from benchmarks import neutral_hostile_determinism_repair_v6 as REPAIR
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_release_product as P

MEDIUM_MAX = 256 * 1024
ROUNDS = 5
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


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


def _measure_row(source: Path, work: Path) -> tuple[list[dict], list[dict], list[dict]]:
    r24_rows: list[dict] = []
    zip_rows: list[dict] = []
    zstd_rows: list[dict] = []
    order = ["r24", "zip", "zstd"]
    for round_index in range(ROUNDS):
        rotated = order[round_index % len(order):] + order[: round_index % len(order)]
        results: dict[str, dict] = {}
        for name in rotated:
            if name == "r24":
                results[name] = _verified_shipping_r24(source, work / f"r24-{round_index}.cmpct")
            elif name == "zip":
                results[name] = EXT._zip(
                    source,
                    work / f"zip-{round_index}.zip",
                    work / f"zip-out-{round_index}",
                )
            else:
                zstd_work = work / f"zstd-work-{round_index}"
                zstd_work.mkdir(parents=True, exist_ok=True)
                results[name] = EXT._tar_zstd(
                    source,
                    work / f"zstd-{round_index}.tar.zst",
                    work / f"zstd-out-{round_index}",
                    zstd_work,
                )
        r24_rows.append(results["r24"])
        zip_rows.append(results["zip"])
        zstd_rows.append(results["zstd"])
    return r24_rows, zip_rows, zstd_rows


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
            r24_rows, zip_rows, zstd_rows = _measure_row(source, w)

        first = r24_rows[0]
        r24_bytes = int(first["archive_bytes"])
        tree = first["tree_sha256"]
        deterministic_bytes = all(int(row["archive_bytes"]) == r24_bytes for row in r24_rows)
        same_tree = all(row["tree_sha256"] == tree for row in r24_rows)
        zip_size_deterministic = len({int(row["archive_bytes"]) for row in zip_rows}) == 1
        zstd_size_deterministic = len({int(row["archive_bytes"]) for row in zstd_rows}) == 1
        zip_bytes = int(zip_rows[0]["archive_bytes"])
        zstd_bytes = int(zstd_rows[0]["archive_bytes"])
        r24_create = _median(r24_rows, "complete_create_s")
        zip_create = _median(zip_rows, "create_s")
        zstd_create = _median(zstd_rows, "create_s")

        beats_zip_size = r24_bytes < zip_bytes
        beats_zstd_size = r24_bytes < zstd_bytes
        beats_zip_create = r24_create < zip_create
        beats_zstd_create = r24_create < zstd_create
        strict_four_way = beats_zip_size and beats_zstd_size and beats_zip_create and beats_zstd_create
        rows.append({
            "label": label,
            "positive_target": positive,
            "rounds": ROUNDS,
            "shipping_r24": {
                **first,
                "median_complete_create_s": r24_create,
                "complete_create_samples_s": [float(row["complete_create_s"]) for row in r24_rows],
            },
            "comparators": {
                "zip_deflate9": {
                    "archive_bytes": zip_bytes,
                    "median_create_s": zip_create,
                    "create_samples_s": [float(row["create_s"]) for row in zip_rows],
                },
                "tar_zstd19_solid": {
                    "archive_bytes": zstd_bytes,
                    "median_create_s": zstd_create,
                    "create_samples_s": [float(row["create_s"]) for row in zstd_rows],
                },
            },
            "deterministic_archive_bytes": deterministic_bytes,
            "same_verified_tree": same_tree,
            "comparator_archive_sizes_deterministic": zip_size_deterministic and zstd_size_deterministic,
            "beats_zip_size": beats_zip_size,
            "beats_zstd19_size": beats_zstd_size,
            "beats_zip_create": beats_zip_create,
            "beats_zstd19_create": beats_zstd_create,
            "strict_four_way_win": strict_four_way,
        })
        print(
            json.dumps(
                {
                    "label": label,
                    "bytes": r24_bytes,
                    "median_create_s": r24_create,
                    "zip_create_s": zip_create,
                    "zstd_create_s": zstd_create,
                    "four_way": strict_four_way,
                },
                separators=(",", ":"),
            ),
            flush=True,
        )

    positives = [r for r in rows if r["positive_target"]]
    controls = [r for r in rows if not r["positive_target"]]
    gate = {
        "all_verified_tree_equal": all(r["same_verified_tree"] for r in rows),
        "all_archive_bytes_deterministic": all(r["deterministic_archive_bytes"] for r in rows),
        "all_comparator_archive_sizes_deterministic": all(r["comparator_archive_sizes_deterministic"] for r in rows),
        "positive_rows_strict_four_way": all(r["strict_four_way_win"] for r in positives),
        # The negative control is intentionally allowed to remain a Zstd size loss; this lane only proves that
        # r24-v4 itself stays deterministic and verified there. The all-15 external frontier remains authoritative.
        "negative_controls_verified_and_deterministic": all(
            r["same_verified_tree"] and r["deterministic_archive_bytes"] for r in controls
        ),
    }
    gate["shipping_regression_passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-r24-medium-binary-pack-regression-v3",
        "contract": {
            "grammar": "existing canonical r24 S_PACK only",
            "shipping_micro_pack_max_file_bytes": MEDIUM_MAX,
            "shipping_extra_pack_hint": ".bin",
            "locality_policy": "shipping r24 micro_pack_target remains min(2 MiB, 8x largest regular member)",
            "timing_policy": f"{ROUNDS} rotated same-runner rounds; median; r24 timing includes build + mandatory strong verification",
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
