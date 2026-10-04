from __future__ import annotations

"""Exact A/B for eliminating the remaining full-payload copy from direct C25CC01 extraction.

Both arms consume the same already-built archive, use the same authenticated compact-control expansion and mature r24
reader, and include transactional publication inside timing.  The mmap arm differs only by exposing the unchanged
physical payload span through a read-only memoryview instead of Path.read_bytes()+payload slicing.  Research-only.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from experiments import entropygraph_v030_r24_compact_control_direct_extract as DIRECT
from experiments import entropygraph_v030_r24_compact_control_mmap_extract as MMAP
from experiments import entropygraph_v030_r24_compact_control_profile as CC

ROUNDS = 9


def _fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for i in range(384):
        p = root / "records" / f"group-{i // 32:02d}" / f"measurement-{i:04d}.bin"
        p.parent.mkdir(parents=True, exist_ok=True)
        seed = (f"row={i:04d};stable=1\n").encode()
        p.write_bytes((seed * ((32 * 1024 + len(seed) - 1) // len(seed)))[: 32 * 1024])


def _tree_digest(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix().encode()
        if path.is_dir():
            h.update(b"d\0" + rel + b"\0")
        elif path.is_symlink():
            h.update(b"l\0" + rel + b"\0" + path.readlink().as_posix().encode() + b"\0")
        elif path.is_file():
            raw = path.read_bytes()
            h.update(b"f\0" + rel + b"\0" + len(raw).to_bytes(8, "little") + hashlib.sha256(raw).digest())
    return h.hexdigest()


def _run_once(kind: str, archive: Path, dst: Path) -> tuple[float, str]:
    if dst.exists():
        shutil.rmtree(dst)
    t0 = time.perf_counter()
    if kind == "direct":
        DIRECT.extract(archive, dst)
    elif kind == "mmap":
        MMAP.extract(archive, dst)
    else:
        raise ValueError(kind)
    elapsed = time.perf_counter() - t0
    return elapsed, _tree_digest(dst)


def run(work_root: Path) -> dict:
    work_root.mkdir(parents=True, exist_ok=True)
    src = work_root / "source"
    shutil.rmtree(src, ignore_errors=True)
    _fixture(src)
    source_tree = _tree_digest(src)
    archive = work_root / "candidate.cmpct"
    archive.unlink(missing_ok=True)
    build = CC.build(src, archive)
    verified = CC.strong_verify(archive)
    if not verified.get("ok"):
        raise RuntimeError(f"candidate failed strong verification: {verified!r}")

    for kind, fn in (("direct", DIRECT.extract), ("mmap", MMAP.extract)):
        warm = work_root / f"warm-{kind}"
        fn(archive, warm)
        shutil.rmtree(warm)

    samples = {"direct": [], "mmap": []}
    trees = {"direct": [], "mmap": []}
    for round_idx in range(ROUNDS):
        order = ("direct", "mmap") if round_idx % 2 == 0 else ("mmap", "direct")
        for kind in order:
            elapsed, tree = _run_once(kind, archive, work_root / f"{kind}-{round_idx}")
            samples[kind].append(elapsed)
            trees[kind].append(tree)

    direct = statistics.median(samples["direct"])
    mapped = statistics.median(samples["mmap"])
    exact = all(tree == source_tree for rows in trees.values() for tree in rows)
    return {
        "schema": "cmpct-v030-c25cc01-mmap-extract-oracle-v1",
        "contract": {
            "rounds": ROUNDS,
            "same_archive_bytes": True,
            "same_authenticated_control_expansion": True,
            "same_mature_r24_decoder": True,
            "direct_full_archive_read": True,
            "direct_physical_payload_copy": True,
            "mmap_full_archive_read": False,
            "mmap_physical_payload_copy": False,
            "publication_inside_timing": True,
            "logical_output_digest_inside_timing": False,
            "archive_bytes_changed": False,
            "selector_change": False,
            "release_credit": False,
        },
        "candidate": {
            "archive_bytes": archive.stat().st_size,
            "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "tree_sha256": verified["tree_sha256"],
            "build_profile": build["format_profile"],
        },
        "samples_s": samples,
        "median_s": {"direct": direct, "mmap": mapped},
        "mmap_over_direct": mapped / direct,
        "saving_s": direct - mapped,
        "speedup_fraction": 1.0 - mapped / direct,
        "source_tree_digest": source_tree,
        "all_outputs_exact": exact,
        "promotion_signal": bool(exact and mapped < direct),
        "release_credit": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.work_root is None:
        with tempfile.TemporaryDirectory(prefix="cmpct-v030-c25-mmap-extract-") as td:
            result = run(Path(td))
    else:
        result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["all_outputs_exact"]:
        raise SystemExit("mmap extraction changed logical output")


if __name__ == "__main__":
    main()
