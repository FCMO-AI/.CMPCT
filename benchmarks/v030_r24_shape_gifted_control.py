from __future__ import annotations

"""Gifted-control oracle for net canonical-r24 shape-prewalk wall.

A direct helper timer can overstate removable wall if the helper warms filesystem metadata
for Builder.scan. This lower-rung oracle keeps the promoted r24 wrapper and replaces only
_regular_user_shape with already-established exact shape facts during the gifted arm.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_r24_shape_prewalk_attribution_v2 as V2
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_product_base as BASE


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _build(stage: Path, archive: Path, gifted: tuple[int, int] | None) -> dict:
    original = BASE._regular_user_shape
    if gifted is not None:
        BASE._regular_user_shape = lambda _root: gifted
    started = time.perf_counter()
    try:
        stats = dict(PRODUCT._locality_bounded_r24_build(stage, archive))
    finally:
        wall_s = time.perf_counter() - started
        BASE._regular_user_shape = original
    return {
        "gifted": gifted is not None,
        "outer_wall_s": wall_s,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256(archive),
        "regular_user_files": int(stats["regular_user_files"]),
        "largest_regular_bytes": int(stats["locality_selected_member_bytes"]),
        "micro_pack_target_release_bytes": int(stats["micro_pack_target_release_bytes"]),
        "large_file_chunk_policy": stats["large_file_chunk_policy"],
        "dead_dictionary_elision": stats.get("r24_dead_dictionary_elision"),
    }


def _measure(label: str, source: Path, work_root: Path, repetitions: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-r24-shape-gift-", dir=work_root) as td:
        td_path = Path(td)
        stage = V2.EXT._normalized_stage(source, td_path)
        if V2.EXT._tree(stage) != V2.EXT._tree(source):
            raise RuntimeError(f"normalized stage changed tree for {label}")
        gifted = tuple(map(int, BASE._regular_user_shape(stage)))
        rows = []
        outputs = td_path / "outputs"
        outputs.mkdir()
        for rep in range(repetitions):
            order = (None, gifted) if rep % 2 == 0 else (gifted, None)
            for slot, facts in enumerate(order):
                archive = outputs / f"r{rep:02d}-s{slot}-{'g' if facts else 'c'}.cmpct"
                row = _build(stage, archive, facts)
                row["repetition"] = rep
                row["pair_slot"] = slot
                rows.append(row)

        identities = {(r["archive_bytes"], r["archive_sha256"]) for r in rows}
        policy = {
            (
                r["regular_user_files"], r["largest_regular_bytes"],
                r["micro_pack_target_release_bytes"], r["large_file_chunk_policy"],
                r["dead_dictionary_elision"],
            )
            for r in rows
        }
        if len(identities) != 1 or len(policy) != 1:
            raise RuntimeError(f"gifted/control semantic drift for {label}")

        control = [r["outer_wall_s"] for r in rows if not r["gifted"]]
        gift = [r["outer_wall_s"] for r in rows if r["gifted"]]
        control_med = statistics.median(control)
        gift_med = statistics.median(gift)
        saving = control_med - gift_med
        gap = float(V2.INHERITED_GAPS_S[label])
        return {
            "label": label,
            "gifted_shape": {"regular_files": gifted[0], "largest_regular_bytes": gifted[1]},
            "archive_bytes": rows[0]["archive_bytes"],
            "archive_sha256": rows[0]["archive_sha256"],
            "control_outer_wall_s_raw": control,
            "gifted_outer_wall_s_raw": gift,
            "control_outer_wall_s_median": control_med,
            "gifted_outer_wall_s_median": gift_med,
            "net_outer_wall_saving_s": saving,
            "net_saving_over_inherited_gap": saving / gap,
            "material_net_saving_10pct_gap": saving >= 0.10 * gap,
            "rows": rows,
        }


def run(work_root: Path, repetitions: int) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    sources = V2._build_sources(work_root)
    rows = [_measure(label, sources[label], work_root, repetitions) for label in V2.TARGETS]
    material = [r["label"] for r in rows if r["material_net_saving_10pct_gap"]]
    return {
        "schema": "cmpct-v030-r24-shape-gifted-control-v1",
        "authority_head": "496c96b40e09b6cd9a4eb81af2ec52db1caed354",
        "preregistration": "benchmarks/history/2026-10-01-v030-r24-shape-gifted-control-prereg.json",
        "rows": rows,
        "decision": "RETIRE_SHAPE_PREWALK_REUSE" if not material else "NET_MATERIAL_ROWS:" + ",".join(material),
        "claim_boundary": "gifted oracle; no product/release credit",
        "release_credit": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-shape-gifted"))
    p.add_argument("--repetitions", type=int, default=7)
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-shape-gifted-control.json"))
    a = p.parse_args()
    if a.repetitions < 3:
        p.error("--repetitions must be >= 3")
    result = run(a.work_root, a.repetitions)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "rows": [
        {"label": r["label"], "net_outer_wall_saving_s": r["net_outer_wall_saving_s"],
         "net_saving_over_inherited_gap": r["net_saving_over_inherited_gap"]}
        for r in result["rows"]]}, indent=2))


if __name__ == "__main__":
    main()
