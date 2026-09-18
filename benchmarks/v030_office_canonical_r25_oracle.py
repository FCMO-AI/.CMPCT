from __future__ import annotations

"""Office-only oracle for the canonical-r25 contender shadowed by the v0.29 fallback.

This is deliberately *not* a selector-bug presumption. The canonical parent is required
to preserve the accepted v0.29 zero-byte floor, so an r25 contender that beats r24 and
Zstd-19 but regresses v0.29 is still correctly non-promotable. The oracle separates
those cases on the frozen repair-v6 Office tree and changes no shipping policy.
"""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time

from benchmarks import neutral_hostile_determinism_repair_v6 as REPAIR
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_canonical_manifest_candidate as CAND

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TREE = "aac7de772b9f93d5b54ca30e07497574bf61d76c2288077627163c8378823c4b"
EXPECTED_FILES = 20
EXPECTED_LOGICAL_BYTES = 16_063_798
SHIPPING_R24_BYTES = 15_445_236
# Same-run current v0.29 fallback observed inside the exact-head external frontier.
CURRENT_V029_FLOOR_BYTES = 5_954_226
ZSTD19_BYTES = 8_312_879
SEVENZIP_BYTES = 7_455_748


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _build_office(root: Path) -> dict:
    REPAIR._install_producer_hooks()
    REPAIR.BASE.corpus_office(root)
    REPAIR._normalize_workload("office_workspace", root)
    files = sorted(p for p in root.rglob("*") if p.is_file())
    logical = sum(p.stat().st_size for p in files)
    tree = REPAIR.BASE.treehash(root)
    if tree != EXPECTED_TREE or len(files) != EXPECTED_FILES or logical != EXPECTED_LOGICAL_BYTES:
        raise RuntimeError(f"Office substrate drift: tree={tree} files={len(files)} logical={logical}")
    return {"tree_sha256": tree, "files": len(files), "logical_bytes": logical}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    source = work_root / "office_workspace"
    source.mkdir(parents=True)
    substrate = _build_office(source)
    archive = work_root / "office-canonical-r25-only.cmpct"
    started = time.perf_counter()
    stats = CAND.build_ablation(source, archive, "combined")
    create_s = time.perf_counter() - started

    revision, profile = CANON._profile_for_archive(archive)
    if revision != CANON.REVISION:
        raise RuntimeError(f"oracle emitted non-r25 profile: {revision!r}/{profile!r}")
    verified = CAND.strong_verify(archive)
    semantic_tree = CAND.treehash(source)
    if not verified.get("ok") or verified.get("tree_sha256") != semantic_tree:
        raise RuntimeError(f"canonical r25 Office verification failed: {verified!r}")

    worst_amp = 0.0
    for row in CAND.list_members(archive):
        if row.get("kind") == "file":
            _raw, read_stats = CAND.read_member_with_stats(archive, row["path"])
            worst_amp = max(worst_amp, float(read_stats["decoded_context_amplification"]))
    if worst_amp > 8.0:
        raise RuntimeError(f"canonical r25 Office candidate exceeded locality: {worst_amp:.6f}x")

    archive_bytes = archive.stat().st_size
    beats_r24 = archive_bytes < SHIPPING_R24_BYTES
    beats_v029 = archive_bytes <= CURRENT_V029_FLOOR_BYTES
    beats_zstd = archive_bytes < ZSTD19_BYTES
    if beats_r24 and beats_v029 and beats_zstd:
        decision = "CANONICAL_R25_ZERO_REGRESSION_ESCAPE_PROVEN"
    elif beats_r24 and beats_zstd and not beats_v029:
        decision = "CANONICAL_R25_BEATS_WORLD_CONTROLS_BUT_REGRESSES_V029"
    else:
        decision = "CANONICAL_R25_ESCAPE_INSUFFICIENT"

    return {
        "schema": "cmpct-v030-office-canonical-r25-oracle-v2",
        "source_commit": _source_commit(),
        "substrate": "neutral-hostile-determinism-repair-v6",
        "substrate_evidence": substrate,
        "format_revision": revision,
        "format_profile": profile,
        "selected": stats.get("selected"),
        "candidate_set": stats.get("candidate_set"),
        "archive_bytes": archive_bytes,
        "create_s": create_s,
        "max_member_read_amplification": worst_amp,
        "within_locality_8x": True,
        "strong_verify_ok": True,
        "strong_verify_tree_exact": True,
        "shipping_r24_control_bytes": SHIPPING_R24_BYTES,
        "current_v029_floor_control_bytes": CURRENT_V029_FLOOR_BYTES,
        "zstd19_control_bytes": ZSTD19_BYTES,
        "sevenzip_control_bytes": SEVENZIP_BYTES,
        "saving_vs_shipping_r24_bytes": SHIPPING_R24_BYTES - archive_bytes,
        "saving_vs_current_v029_bytes": CURRENT_V029_FLOOR_BYTES - archive_bytes,
        "saving_vs_zstd19_bytes": ZSTD19_BYTES - archive_bytes,
        "saving_vs_7z_bytes": SEVENZIP_BYTES - archive_bytes,
        "beats_shipping_r24": beats_r24,
        "preserves_v029_zero_regression": beats_v029,
        "beats_zstd19": beats_zstd,
        "beats_7z": archive_bytes < SEVENZIP_BYTES,
        "decision": decision,
        "release_credit": False,
        "claim_boundary": "Office-only canonical-r25 materialization oracle. A competitor win is not promotable if it regresses the inherited v0.29 byte floor; all-15/recovery/native/platform authority remains separate.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
