from __future__ import annotations

"""Harder deterministic corpus for CMPCT multi-root mosaic research.

Unlike v1, the positive cases do not hand the encoder pristine segment copies.  Targets inherit regions
from several roots and then undergo sparse rewrites, insertions, record-level conflict resolution,
reordering, or source-like edits.  Controls include compressed-stream avalanche, a strong single parent,
false neighbors, random data, excessive root diversity, and metadata-dominated small targets.

Footnote: v1 remains intentionally preserved.  A research corpus becoming “too easy” after the first
result is evidence about the benchmark, not permission to delete the result that revealed the weakness.
"""

import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import zlib

SEED = 0x29BAD5EED


def _rng(tag: str) -> random.Random:
    salt = int.from_bytes(hashlib.sha256(tag.encode()).digest()[:8], "little")
    return random.Random(SEED ^ salt)


def _bytes(tag: str, n: int) -> bytes:
    rng = _rng(tag)
    return bytes(rng.getrandbits(8) for _ in range(n))


def _reset(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)


def _sparse_rewrite(data: bytes, tag: str, *, every: int, span: int, start: int = 0) -> bytes:
    out = bytearray(data)
    counter = 0
    for pos in range(start, len(out), every):
        patch = hashlib.sha256(f"{tag}:{counter}".encode()).digest()[:span]
        end = min(len(out), pos + len(patch))
        out[pos:end] = patch[: end - pos]
        counter += 1
    return bytes(out)


def noisy_two_parent_merge(root: Path) -> None:
    p = root / "01_noisy_two_parent_merge"; _reset(p)
    ancestor = _bytes("noisy-ancestor", 320 * 1024)
    a = bytearray(ancestor); b = bytearray(ancestor)
    # Each branch rewrites alternating 20 KiB regions rather than whole benchmark-aligned chunks.
    region = 20 * 1024
    for index, start in enumerate(range(0, len(ancestor), region)):
        replacement = _bytes(f"noisy-branch-{index % 2}-{index}", min(region, len(ancestor) - start))
        if index % 2 == 0:
            a[start : start + len(replacement)] = replacement
        else:
            b[start : start + len(replacement)] = replacement
    root_a, root_b = bytes(a), bytes(b)
    merged = bytearray()
    for index, start in enumerate(range(0, len(ancestor), region)):
        end = min(len(ancestor), start + region)
        merged += (root_a if index % 2 == 0 else root_b)[start:end]
    # Conflict-resolution edits puncture otherwise reusable ranges every few KiB.
    target = _sparse_rewrite(bytes(merged), "noisy-merge-resolution", every=3079, span=19, start=997)
    (p / "root-a.bin").write_bytes(root_a)
    (p / "root-b.bin").write_bytes(root_b)
    (p / "target-merge.bin").write_bytes(target)


def shifted_reordered_merge(root: Path) -> None:
    p = root / "02_shifted_reordered_merge"; _reset(p)
    left = [_bytes(f"shift-left-{i}", 24 * 1024 + (i % 3) * 211) for i in range(10)]
    right = [_bytes(f"shift-right-{i}", 24 * 1024 + (i % 5) * 173) for i in range(10)]
    (p / "root-left.bin").write_bytes(b"".join(left))
    (p / "root-right.bin").write_bytes(b"".join(right))
    order = [8, 1, 6, 3, 9, 0, 5, 2, 7, 4]
    parts = [(left if i % 3 else right)[i] for i in order]
    target = b"".join(parts)
    target = target[:43_211] + _bytes("shift-insert-a", 913) + target[43_211:]
    target = target[:177_777] + _bytes("shift-insert-b", 2_117) + target[177_777:]
    target = _sparse_rewrite(target, "shift-post-merge", every=8191, span=11, start=2043)
    (p / "target-reordered.bin").write_bytes(target)


def record_store_conflict_merge(root: Path) -> None:
    p = root / "03_record_store_conflict_merge"; _reset(p)
    rng = _rng("record-store")
    base_records = []
    for key in range(2400):
        payload = bytes(rng.getrandbits(8) for _ in range(192))
        base_records.append(key.to_bytes(4, "little") + payload + b"\n")

    def branch(which: str) -> list[bytes]:
        rows = list(base_records)
        parity = 0 if which == "a" else 1
        for key in range(parity, len(rows), 4):
            row = bytearray(rows[key])
            row[17:33] = hashlib.sha256(f"{which}:{key}".encode()).digest()[:16]
            rows[key] = bytes(row)
        return rows

    a = branch("a"); b = branch("b")
    (p / "root-a.bin").write_bytes(b"".join(a))
    (p / "root-b.bin").write_bytes(b"".join(b))
    merged = [a[key] if key % 4 == 0 else b[key] if key % 4 == 1 else base_records[key] for key in range(2400)]
    # Compaction changes physical record order while preserving the inherited record bytes.
    order = sorted(range(len(merged)), key=lambda key: hashlib.blake2b(key.to_bytes(4, "little"), digest_size=8).digest())
    target = b"".join(merged[key] for key in order)
    target = _sparse_rewrite(target, "record-post-compact", every=19_997, span=7, start=333)
    (p / "target-compacted.bin").write_bytes(target)


def source_like_merge(root: Path) -> None:
    p = root / "04_source_like_merge"; _reset(p)

    def make_file(branch: str, module: int) -> bytes:
        lines = [f"# package module={module} branch={branch}\n", "from __future__ import annotations\n"]
        for fn in range(120):
            lines += [
                f"def operation_{module}_{fn}(item: int, *, retry: bool = False) -> int:\n",
                f"    limit = {1000 + module * 7 + fn}\n",
                f"    value = (item * {fn + 11} + {module * 31}) % limit\n",
                f"    return value + ({1 if branch == 'a' else 2} if retry else 0)\n\n",
            ]
        return "".join(lines).encode()

    a = [make_file("a", i) for i in range(12)]
    b = [make_file("b", i) for i in range(12)]
    (p / "root-a.bin").write_bytes(b"".join(a))
    (p / "root-b.bin").write_bytes(b"".join(b))
    target_parts = []
    for module in range(12):
        chosen = a[module] if module in {0, 2, 3, 7, 8, 11} else b[module]
        chosen = chosen.replace(b"retry: bool = False", b"retry: bool = True", 2 + module % 4)
        target_parts.append(chosen)
    (p / "target-main.bin").write_bytes(b"".join(target_parts))


def compressed_stream_avalan(root: Path) -> None:
    p = root / "05_compressed_stream_avalan"; _reset(p)
    plain = _bytes("compressed-plain", 512 * 1024)
    for i in range(4):
        mutated = _sparse_rewrite(plain, f"compressed-root-{i}", every=65_537, span=3, start=i * 101)
        (p / f"root-{i}.bin").write_bytes(zlib.compress(mutated, 9))
    target_plain = _sparse_rewrite(plain, "compressed-target", every=61_013, span=5, start=777)
    (p / "target-compressed.bin").write_bytes(zlib.compress(target_plain, 9))


def single_parent_noisy_control(root: Path) -> None:
    p = root / "06_single_parent_noisy_control"; _reset(p)
    best = _bytes("single-noisy-best", 320 * 1024)
    target = _sparse_rewrite(best, "single-noisy-target", every=4093, span=13, start=211)
    (p / "root-best.bin").write_bytes(best)
    for i in range(3):
        (p / f"root-distractor-{i}.bin").write_bytes(_bytes(f"single-noisy-distractor-{i}", len(best)))
    (p / "target-near.bin").write_bytes(target)


def false_neighbors_control(root: Path) -> None:
    p = root / "07_false_neighbors_control"; _reset(p)
    header = (b"schema=v3|tenant=public|" * 400)[:8192]
    footer = (b"index-footer|checksum-placeholder|" * 300)[:8192]
    for i in range(4):
        body = _bytes(f"false-v2-root-{i}", 300 * 1024)
        (p / f"root-{i}.bin").write_bytes(header + body + footer)
    (p / "target-independent.bin").write_bytes(header + _bytes("false-v2-target", 300 * 1024) + footer)


def incompressible_control(root: Path) -> None:
    p = root / "08_incompressible_control"; _reset(p)
    for i in range(4):
        (p / f"root-{i}.bin").write_bytes(_bytes(f"hard-random-root-{i}", 320 * 1024))
    (p / "target-random.bin").write_bytes(_bytes("hard-random-target", 320 * 1024))


def root_diversity_pressure(root: Path) -> None:
    p = root / "09_root_diversity_pressure"; _reset(p)
    roots = []
    for i in range(8):
        data = _bytes(f"diverse-root-{i}", 192 * 1024)
        roots.append(data)
        (p / f"root-{i}.bin").write_bytes(data)
    # Five roots contribute; the encoder may index only four.  A bounded design must accept leaving
    # some reusable information on the table instead of silently widening candidate fanout.
    target = b"".join(roots[i][i * 20_000 : i * 20_000 + 32_000] for i in range(5))
    target = _sparse_rewrite(target, "diverse-target", every=5003, span=9, start=109)
    (p / "target-five-way.bin").write_bytes(target)


def small_metadata_control(root: Path) -> None:
    p = root / "10_small_metadata_control"; _reset(p)
    a = _bytes("small-a", 2048); b = _bytes("small-b", 2048)
    target = a[:900] + b[900:1500] + a[1500:]
    (p / "root-a.bin").write_bytes(a)
    (p / "root-b.bin").write_bytes(b)
    (p / "target-small.bin").write_bytes(target)


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
        noisy_two_parent_merge,
        shifted_reordered_merge,
        record_store_conflict_merge,
        source_like_merge,
        compressed_stream_avalan,
        single_parent_noisy_control,
        false_neighbors_control,
        incompressible_control,
        root_diversity_pressure,
        small_metadata_control,
    ):
        fn(root)
    rows = []
    for workload in sorted(p for p in root.iterdir() if p.is_dir()):
        roots = sorted(workload.glob("root-*.bin")); targets = sorted(workload.glob("target-*.bin"))
        rows.append({
            "name": workload.name,
            "roots": len(roots),
            "targets": len(targets),
            "logical_bytes": sum(p.stat().st_size for p in roots + targets),
            "tree_sha256": tree_hash(workload),
        })
    return {"schema": "cmpct-mosaic-stress-v2", "seed": SEED, "workloads": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("CMPCT_Mosaic_Stress_v2"))
    args = parser.parse_args()
    print(json.dumps(build(args.root), indent=2))
