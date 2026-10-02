from __future__ import annotations

"""Exact-source phase attribution for the canonical-r24 source-shape prewalk.

This is an evidence instrument, not a candidate implementation. It executes the current
authority r24 builder unchanged while timing only the release-only _regular_user_shape
call that precedes Builder.build()/Builder.scan(). A paired uninstrumented control proves
that the wrapper itself does not change archive bytes or materially distort total create
wall.

The workload generator and normalization path are exactly the external-competitor corpus
path. No benchmark threshold, corpus, comparator, product policy, or archive format is
modified here.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product_base as R24

TARGETS = (
    "neutral_hostile_v1/01_developer_repository",
    "neutral_hostile_v1/06_incremental_backups",
    "neutral_hostile_v1/08_many_tiny_files",
    "resemblance_hostile_v1/04_deflate_family",
)

INHERITED_GAPS_S = {
    "neutral_hostile_v1/01_developer_repository": 0.101520,
    "neutral_hostile_v1/06_incremental_backups": 0.231840,
    "neutral_hostile_v1/08_many_tiny_files": 0.080497384,
    "resemblance_hostile_v1/04_deflate_family": 0.014400,
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _build_sources(work_root: Path) -> dict[str, Path]:
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_r24_shape_neutral",
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_r24_shape_hostile",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_r24_shape_repair")
    repair.install_generation_hooks(neutral)

    roots = (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    )
    selected: dict[str, Path] = {}
    for suite, builder, root in roots:
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            label = f"{suite}/{workload.name}"
            if label not in TARGETS:
                continue
            expected_tree = accepted[(suite, workload.name)]["tree_sha256"]
            got_tree = EXT._tree(workload)
            if got_tree != expected_tree:
                raise RuntimeError(
                    f"source drift for {label}: {got_tree} != accepted {expected_tree}"
                )
            selected[label] = workload
    missing = sorted(set(TARGETS).difference(selected))
    if missing:
        raise RuntimeError(f"missing target workloads: {missing}")
    return selected


def _one_build(stage: Path, archive: Path, *, instrument_shape: bool) -> dict:
    original = R24._regular_user_shape
    shape_calls: list[dict] = []

    def measured(root: Path):
        started = time.perf_counter()
        result = original(root)
        elapsed = time.perf_counter() - started
        shape_calls.append(
            {
                "wall_s": elapsed,
                "regular_files": int(result[0]),
                "largest_regular_bytes": int(result[1]),
            }
        )
        return result

    if instrument_shape:
        R24._regular_user_shape = measured
    started = time.perf_counter()
    try:
        stats = dict(R24._locality_bounded_r24_build(stage, archive))
    finally:
        wall_s = time.perf_counter() - started
        R24._regular_user_shape = original

    if instrument_shape and len(shape_calls) != 1:
        raise RuntimeError(f"expected exactly one source-shape prewalk, observed {shape_calls!r}")
    if not instrument_shape and shape_calls:
        raise RuntimeError("control unexpectedly recorded a shape call")

    return {
        "instrumented": instrument_shape,
        "outer_wall_s": wall_s,
        "reported_r24_create_s": float(stats["create_s"]),
        "shape": shape_calls[0] if shape_calls else None,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256(archive),
        "regular_user_files": int(stats["regular_user_files"]),
        "locality_selected_member_bytes": int(stats["locality_selected_member_bytes"]),
        "micro_pack_target_default_bytes": int(stats["micro_pack_target_default_bytes"]),
        "micro_pack_target_release_bytes": int(stats["micro_pack_target_release_bytes"]),
        "micro_pack_max_file_release_bytes": int(stats["micro_pack_max_file_release_bytes"]),
        "large_file_chunk_policy": stats["large_file_chunk_policy"],
        "release_byte_knobs": stats["release_byte_knobs"],
    }


def _measure_label(label: str, source: Path, work_root: Path, repetitions: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-r24-shape-stage-", dir=work_root) as td:
        td_path = Path(td)
        stage = EXT._normalized_stage(source, td_path)
        expected_tree = EXT._tree(source)
        if EXT._tree(stage) != expected_tree:
            raise RuntimeError(f"normalized stage changed tree for {label}")

        rows: list[dict] = []
        outputs = td_path / "outputs"
        outputs.mkdir()
        # Alternate pair order to avoid assigning all cache/order bias to the instrumented side.
        for rep in range(repetitions):
            order = (True, False) if rep % 2 == 0 else (False, True)
            for slot, instrument in enumerate(order):
                archive = outputs / f"r{rep:02d}-s{slot}-{'i' if instrument else 'c'}.cmpct"
                row = _one_build(stage, archive, instrument_shape=instrument)
                row["repetition"] = rep
                row["pair_slot"] = slot
                rows.append(row)

        identities = {(row["archive_bytes"], row["archive_sha256"]) for row in rows}
        policy_facts = {
            (
                row["regular_user_files"],
                row["locality_selected_member_bytes"],
                row["micro_pack_target_default_bytes"],
                row["micro_pack_target_release_bytes"],
                row["micro_pack_max_file_release_bytes"],
                row["large_file_chunk_policy"],
                row["release_byte_knobs"],
            )
            for row in rows
        }
        if len(identities) != 1:
            raise RuntimeError(f"instrument/control archive identity mismatch for {label}: {identities}")
        if len(policy_facts) != 1:
            raise RuntimeError(f"instrument/control policy mismatch for {label}: {policy_facts}")

        instrumented = [row for row in rows if row["instrumented"]]
        controls = [row for row in rows if not row["instrumented"]]
        shape_wall = [float(row["shape"]["wall_s"]) for row in instrumented]
        instrument_outer = [float(row["outer_wall_s"]) for row in instrumented]
        control_outer = [float(row["outer_wall_s"]) for row in controls]
        gap = float(INHERITED_GAPS_S[label])
        median_shape = statistics.median(shape_wall)
        return {
            "label": label,
            "repetitions_per_side": repetitions,
            "archive_bytes": rows[0]["archive_bytes"],
            "archive_sha256": rows[0]["archive_sha256"],
            "policy": {
                "regular_user_files": rows[0]["regular_user_files"],
                "largest_regular_bytes": rows[0]["locality_selected_member_bytes"],
                "micro_pack_target_default_bytes": rows[0]["micro_pack_target_default_bytes"],
                "micro_pack_target_release_bytes": rows[0]["micro_pack_target_release_bytes"],
                "micro_pack_max_file_release_bytes": rows[0]["micro_pack_max_file_release_bytes"],
                "large_file_chunk_policy": rows[0]["large_file_chunk_policy"],
                "release_byte_knobs": rows[0]["release_byte_knobs"],
            },
            "timing": {
                "shape_wall_s_raw": shape_wall,
                "shape_wall_s_median": median_shape,
                "instrumented_outer_wall_s_raw": instrument_outer,
                "instrumented_outer_wall_s_median": statistics.median(instrument_outer),
                "control_outer_wall_s_raw": control_outer,
                "control_outer_wall_s_median": statistics.median(control_outer),
                "instrumented_over_control_median_ratio": (
                    statistics.median(instrument_outer) / statistics.median(control_outer)
                ),
            },
            "inherited_strict_create_gap_s": gap,
            "shape_median_over_inherited_gap": median_shape / gap,
            "material_attribution_10pct_gap": median_shape >= 0.10 * gap,
            "rows": rows,
        }


def run(work_root: Path, repetitions: int) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    sources = _build_sources(work_root)
    results = [
        _measure_label(label, sources[label], work_root, repetitions)
        for label in TARGETS
    ]
    material = [row["label"] for row in results if row["material_attribution_10pct_gap"]]
    return {
        "schema": "cmpct-v030-r24-shape-prewalk-attribution-v1",
        "authority_head": "496c96b40e09b6cd9a4eb81af2ec52db1caed354",
        "preregistration": "benchmarks/history/2026-10-01-v030-r24-shape-prewalk-attribution-prereg.json",
        "instrument": "exact current r24 builder with one wrapped _regular_user_shape call plus paired byte-identical uninstrumented controls",
        "rows": results,
        "decision": (
            "RETIRE_SHAPE_PREWALK_REUSE"
            if not material
            else "NARROW_TO_MATERIAL_ROWS:" + ",".join(material)
        ),
        "release_credit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-shape-prewalk"),
    )
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-shape-prewalk-attribution.json"),
    )
    args = parser.parse_args()
    if args.repetitions < 3:
        raise SystemExit("--repetitions must be >= 3")
    result = run(args.work_root, args.repetitions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "rows": [
                    {
                        "label": row["label"],
                        "shape_wall_s_median": row["timing"]["shape_wall_s_median"],
                        "control_outer_wall_s_median": row["timing"]["control_outer_wall_s_median"],
                        "shape_median_over_inherited_gap": row["shape_median_over_inherited_gap"],
                        "material_attribution_10pct_gap": row["material_attribution_10pct_gap"],
                    }
                    for row in result["rows"]
                ],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
