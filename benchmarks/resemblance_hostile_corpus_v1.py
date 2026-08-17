from __future__ import annotations

"""Deterministic hostile supplement for CMPCT resemblance/delta research.

These workloads exist to falsify the tempting assumptions behind similarity compression: that shared
features imply useful deltas, that CDC always re-synchronizes cheaply, and that a near-duplicate graph
should be allowed to grow without a candidate-work budget.
"""

import argparse
import hashlib
from pathlib import Path
import random
import shutil
import zipfile

SEED = 0x28C0FFEE


def _rng(tag: str) -> random.Random:
    salt = int.from_bytes(hashlib.sha256(tag.encode()).digest()[:8], "little")
    return random.Random(SEED ^ salt)


def _bytes(rng: random.Random, n: int) -> bytes:
    return bytes(rng.getrandbits(8) for _ in range(n))


def _reset(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)


def shifted_versions(root: Path) -> None:
    p = root / "01_shifted_versions"; _reset(p); rng = _rng("shifted")
    blocks = [(_bytes(rng, 1024) if i % 11 else (b"structured-record|" + bytes([i % 251])) * 60) for i in range(1800)]
    base = b"".join(blocks)
    for version in range(18):
        data = bytearray(base)
        insert = (f"version={version};".encode() * (19 + version))
        at = 7000 + version * 7919
        data[at:at] = insert
        for j in range(24):
            pos = (version * 1543 + j * 65537) % len(data)
            data[pos:pos + 17] = hashlib.sha256(f"{version}:{j}".encode()).digest()[:17]
        (p / f"snapshot-{version:02d}.bin").write_bytes(data)


def false_neighbors(root: Path) -> None:
    p = root / "02_false_neighbors"; _reset(p); rng = _rng("false")
    header = (b"COMMON-HEADER\n" * 300)[:4096]
    footer = (b"COMMON-FOOTER\n" * 300)[:4096]
    for i in range(600):
        # Footnote: shared regions deliberately trigger super-features while the large body remains
        # independent. A correct encoder should audition and reject most of these edges.
        body = _bytes(rng, 56 * 1024 + (i % 7) * 113)
        (p / f"object-{i:04d}.bin").write_bytes(header + body + footer)


def boundary_churn(root: Path) -> None:
    p = root / "03_boundary_churn"; _reset(p); rng = _rng("boundary")
    base = bytearray()
    for i in range(700):
        base += (f"record:{i:06d}|tenant={i%37:02d}|status=active|".encode() * 28)
        base += _bytes(rng, 96)
    raw = bytes(base)
    for version in range(12):
        data = bytearray(raw)
        # Repeated one-byte insertions specifically punish aligned fixed-block deltas and test whether
        # the rolling target checksum can re-synchronize after a shift.
        for pos in range(32 * 1024 + version, len(data), 64 * 1024):
            data[pos:pos] = bytes([(version * 17 + pos) & 255])
        (p / f"tree-{version:02d}.dat").write_bytes(data)


def deflate_family(root: Path) -> None:
    p = root / "04_deflate_family"; _reset(p)
    for version in range(14):
        source = p / f"src-{version:02d}"; source.mkdir()
        for i in range(40):
            text = f"module={i};version={version};\n" + ("shared business data row\n" * 900)
            if i % 9 == version % 9:
                text += f"PATCH {version} {i}\n" * 120
            (source / f"member-{i:03d}.txt").write_text(text, encoding="utf-8")
        archive = p / f"bundle-{version:02d}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for child in sorted(source.iterdir()):
                info = zipfile.ZipInfo(child.name, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, child.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        shutil.rmtree(source)


def incompressible(root: Path) -> None:
    p = root / "05_incompressible"; _reset(p); rng = _rng("random")
    for i in range(80):
        (p / f"random-{i:03d}.bin").write_bytes(_bytes(rng, 128 * 1024 + (i % 13) * 257))


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(q for q in root.rglob("*") if q.is_file()):
        rel = path.relative_to(root).as_posix().encode(); data = path.read_bytes()
        h.update(len(rel).to_bytes(4, "little")); h.update(rel)
        h.update(len(data).to_bytes(8, "little")); h.update(data)
    return h.hexdigest()


def build(root: Path) -> dict:
    _reset(root)
    for fn in (shifted_versions, false_neighbors, boundary_churn, deflate_family, incompressible):
        fn(root)
    rows = []
    for workload in sorted(p for p in root.iterdir() if p.is_dir()):
        files = [p for p in workload.rglob("*") if p.is_file()]
        rows.append({"name": workload.name, "files": len(files),
                     "logical_bytes": sum(p.stat().st_size for p in files), "tree_sha256": tree_hash(workload)})
    return {"schema": "cmpct-resemblance-hostile-v1", "seed": SEED, "workloads": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=Path("CMPCT_Resemblance_Hostile_v1"))
    args = parser.parse_args(); import json; print(json.dumps(build(args.root), indent=2))
