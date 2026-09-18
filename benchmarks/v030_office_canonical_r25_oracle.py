from __future__ import annotations

"""Office-only oracle for the canonical-r25 contender hidden by the v0.29 fallback.

The shipping two-level selector can let the inner tournament choose a smaller non-r25
fallback, after which the canonical parent rejects it and publishes r24. This instrument
prices only legal r25 contenders on the frozen repair-v6 Office tree. It changes no
shipping policy and earns no release credit.
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
SHIPPING_BYTES = 15_445_236
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
    decision = "CANONICAL_R25_ESCAPE_PROVEN" if archive_bytes < SHIPPING_BYTES and archive_bytes < ZSTD19_BYTES else "CANONICAL_R25_ESCAPE_INSUFFICIENT"
    return {
        "schema": "cmpct-v030-office-canonical-r25-oracle-v1",
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
        "shipping_control_bytes": SHIPPING_BYTES,
        "zstd19_control_bytes": ZSTD19_BYTES,
        "sevenzip_control_bytes": SEVENZIP_BYTES,
        "saving_vs_shipping_bytes": SHIPPING_BYTES - archive_bytes,
        "saving_vs_zstd19_bytes": ZSTD19_BYTES - archive_bytes,
        "saving_vs_7z_bytes": SEVENZIP_BYTES - archive_bytes,
        "beats_shipping": archive_bytes < SHIPPING_BYTES,
        "beats_zstd19": archive_bytes < ZSTD19_BYTES,
        "beats_7z": archive_bytes < SEVENZIP_BYTES,
        "decision": decision,
        "release_credit": False,
        "claim_boundary": "Office-only canonical-r25 materialization oracle; shipping selection and all-15/recovery/native/platform authority remain unchanged.",
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
    if result["decision"] != "CANONICAL_R25_ESCAPE_PROVEN":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
