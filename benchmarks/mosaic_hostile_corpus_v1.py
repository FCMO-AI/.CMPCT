from __future__ import annotations

"""Deterministic falsification corpus for CMPCT multi-root mosaic resemblance research.

The suite deliberately mixes workloads where several independent roots *should* help with controls where
multi-root indexing should buy nothing.  A research candidate is not allowed to call the mechanism a
win by running only the branch/merge examples it was invented for.

Each workload uses ``root-*.bin`` for admissible direct roots and ``target-*.bin`` for objects the
benchmark must reconstruct.  Names are benchmark structure, not encoder hints: the research harness
loads the declared role only to establish a known depth-1 oracle and then measures actual encoded bytes.
"""

import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil

SEED = 0x29C0FFEE
SEGMENT = 16 * 1024


def _rng(tag: str) -> random.Random:
    salt = int.from_bytes(hashlib.sha256(tag.encode()).digest()[:8], "little")
    return random.Random(SEED ^ salt)


def _bytes(rng: random.Random, n: int) -> bytes:
    return bytes(rng.getrandbits(8) for _ in range(n))


def _reset(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)


def _patch(data: bytes, tag: str, positions: list[int]) -> bytes:
    out = bytearray(data)
    for index, pos in enumerate(positions):
        patch = hashlib.sha256(f"{tag}:{index}".encode()).digest()[:23]
        out[pos : pos + len(patch)] = patch
    return bytes(out)


def _segments(tag: str, count: int = 16) -> list[bytes]:
    rng = _rng(tag)
    return [_bytes(rng, SEGMENT) for _ in range(count)]


def two_parent_branch_merge(root: Path) -> None:
    """Target contains independent edits from two branches of one ancestor."""
    p = root / "01_two_parent_branch_merge"; _reset(p)
    ancestor = _segments("branch-ancestor")
    a = list(ancestor); b = list(ancestor)
    for i in range(0, len(ancestor), 2):
        a[i] = _segments(f"branch-a-{i}", 1)[0]
    for i in range(1, len(ancestor), 2):
        b[i] = _segments(f"branch-b-{i}", 1)[0]
    root_a = b"".join(a); root_b = b"".join(b)
    target = b"".join(a[i] if i % 2 == 0 else b[i] for i in range(len(ancestor)))
    target = _patch(target, "branch-merge", [7_111, 93_017, 201_337])
    (p / "root-a.bin").write_bytes(root_a)
    (p / "root-b.bin").write_bytes(root_b)
    (p / "target-merge.bin").write_bytes(target)


def four_way_cherry_pick(root: Path) -> None:
    """A release image cherry-picks independent regions from four direct roots."""
    p = root / "02_four_way_cherry_pick"; _reset(p)
    roots: list[bytes] = []
    source_segments: list[list[bytes]] = []
    for branch in range(4):
        segs = _segments(f"four-way-{branch}")
        source_segments.append(segs)
        roots.append(b"".join(segs))
        (p / f"root-{branch}.bin").write_bytes(roots[-1])
    # Preserve source offsets while alternating ownership every four segments.  That is representative
    # of a merged binary/package assembled from independently generated sections without manufacturing
    # an easy concatenation of whole roots.
    target_parts = [source_segments[(i // 4) % 4][i] for i in range(16)]
    target = _patch(b"".join(target_parts), "four-way-target", [31_003, 155_551])
    (p / "target-release.bin").write_bytes(target)


def reordered_two_parent_merge(root: Path) -> None:
    """Target both reorders modules and draws them from two roots, attacking aligned block deltas."""
    p = root / "03_reordered_two_parent_merge"; _reset(p)
    left = _segments("reordered-left", 12)
    right = _segments("reordered-right", 12)
    (p / "root-left.bin").write_bytes(b"".join(left))
    (p / "root-right.bin").write_bytes(b"".join(right))
    order = [0, 7, 2, 9, 4, 11, 1, 8, 3, 10, 5, 6]
    parts = [(left if idx % 2 == 0 else right)[idx] for idx in order]
    # One insertion shifts all following target offsets; the rolling matcher must re-synchronize.
    target = b"".join(parts)
    target = target[:71_113] + b"MERGE-MANIFEST|" * 19 + target[71_113:]
    (p / "target-reordered.bin").write_bytes(target)


def source_tree_merge(root: Path) -> None:
    """Code/config-like modules from two branches, not random binary blocks."""
    p = root / "04_source_tree_merge"; _reset(p)

    def module(branch: str, index: int) -> bytes:
        lines = [
            f"# module {index} branch {branch}\n",
            "from __future__ import annotations\n",
            f"DEFAULT_TIMEOUT = {30 + index}\n",
        ]
        for fn in range(44):
            lines.append(f"def task_{index}_{fn}(value: int) -> int:\n")
            lines.append(f"    # deterministic branch={branch} implementation\n")
            lines.append(f"    return (value * {fn + 3} + {index * 17}) % 1000003\n\n")
        text = "".join(lines).encode()
        return (text * ((SEGMENT + len(text) - 1) // len(text)))[:SEGMENT]

    left = [module("left", i) for i in range(16)]
    right = [module("right", i) for i in range(16)]
    (p / "root-left.bin").write_bytes(b"".join(left))
    (p / "root-right.bin").write_bytes(b"".join(right))
    target = b"".join(left[i] if i in {0, 1, 4, 5, 8, 11, 14} else right[i] for i in range(16))
    target = target[:128_000] + b"# merge-resolution: preserve both APIs\n" + target[128_000:]
    (p / "target-main.bin").write_bytes(target)


def single_parent_control(root: Path) -> None:
    """A normal near-duplicate where extra roots should not beat the best one-root representation."""
    p = root / "05_single_parent_control"; _reset(p)
    rng = _rng("single-control")
    best = _bytes(rng, 256 * 1024)
    distractors = [_bytes(_rng(f"single-distractor-{i}"), len(best)) for i in range(3)]
    target = _patch(best, "single-target", [1_003, 71_111, 190_007, 250_001])
    (p / "root-best.bin").write_bytes(best)
    for i, data in enumerate(distractors):
        (p / f"root-distractor-{i}.bin").write_bytes(data)
    (p / "target-near.bin").write_bytes(target)


def false_mosaic_sources(root: Path) -> None:
    """Common headers/footers create sketch temptation but independent bodies should remain literals."""
    p = root / "06_false_mosaic_sources"; _reset(p)
    header = (b"COMMON-MOSAIC-HEADER\n" * 250)[:4096]
    footer = (b"COMMON-MOSAIC-FOOTER\n" * 250)[:4096]
    for i in range(4):
        body = _bytes(_rng(f"false-root-{i}"), 248 * 1024)
        (p / f"root-{i}.bin").write_bytes(header + body + footer)
    target = header + _bytes(_rng("false-target"), 248 * 1024) + footer
    (p / "target-independent.bin").write_bytes(target)


def incompressible_control(root: Path) -> None:
    p = root / "07_incompressible_control"; _reset(p)
    for i in range(4):
        (p / f"root-{i}.bin").write_bytes(_bytes(_rng(f"random-root-{i}"), 256 * 1024))
    (p / "target-random.bin").write_bytes(_bytes(_rng("random-target"), 256 * 1024))


def duplicate_root_pressure(root: Path) -> None:
    """Many redundant candidate roots attack deterministic candidate and source-index bounds."""
    p = root / "08_duplicate_root_pressure"; _reset(p)
    seed = _bytes(_rng("duplicate-root-seed"), 192 * 1024)
    for i in range(12):
        # Tiny differences prevent exact identity while preserving a deliberately hostile candidate set.
        data = _patch(seed, f"dup-root-{i}", [1024 + i * 97, 90_000 + i * 131])
        (p / f"root-{i:02d}.bin").write_bytes(data)
    target = _patch(seed, "dup-target", [17_777, 111_111])
    (p / "target-pressure.bin").write_bytes(target)


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(q for q in root.rglob("*") if q.is_file()):
        rel = path.relative_to(root).as_posix().encode(); data = path.read_bytes()
        h.update(len(rel).to_bytes(4, "little")); h.update(rel)
        h.update(len(data).to_bytes(8, "little")); h.update(data)
    return h.hexdigest()


def build(root: Path) -> dict:
    _reset(root)
    for fn in (
        two_parent_branch_merge,
        four_way_cherry_pick,
        reordered_two_parent_merge,
        source_tree_merge,
        single_parent_control,
        false_mosaic_sources,
        incompressible_control,
        duplicate_root_pressure,
    ):
        fn(root)
    rows = []
    for workload in sorted(p for p in root.iterdir() if p.is_dir()):
        roots = sorted(workload.glob("root-*.bin"))
        targets = sorted(workload.glob("target-*.bin"))
        rows.append(
            {
                "name": workload.name,
                "roots": len(roots),
                "targets": len(targets),
                "logical_bytes": sum(p.stat().st_size for p in roots + targets),
                "tree_sha256": tree_hash(workload),
            }
        )
    return {"schema": "cmpct-mosaic-hostile-v1", "seed": SEED, "workloads": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("CMPCT_Mosaic_Hostile_v1"))
    args = parser.parse_args()
    print(json.dumps(build(args.root), indent=2))
