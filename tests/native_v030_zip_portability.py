#!/usr/bin/env python3
"""Canonical v0.30 ZIP/export interoperability across every publishable revision/profile family."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile
import zipfile

from cmpct.builder import Builder
import generate_v030_canonical_goldens as G


USER_PATH = "dir/hello.bin"


def _regular_manifest() -> tuple[bytes, bytes]:
    raw = (b"cmpct-r25-zip-portability\n" * 19) + bytes(range(64))
    digest = hashlib.sha256(raw).digest()
    manifest = G.pack(
        {
            "v": 1,
            "profile": G.MANIFEST_PROFILE,
            "internal_path": G.INTERNAL,
            "entries": [
                ["dir", "d", 0o755, 1_700_000_000_100_000_001, 1000, 1000, [], None],
                [USER_PATH, "f", 0o640, 1_700_000_000_100_000_002, 1000, 1000, [], [len(raw), digest]],
            ],
        }
    )
    return manifest, raw


def _run(binary: Path, *args: str, check: bool = True):
    result = subprocess.run([str(binary), *args], check=False, capture_output=True)
    if check and result.returncode != 0:
        stdout = result.stdout.decode("utf-8", errors="replace").strip()
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"native command failed rc={result.returncode}: {binary} {' '.join(args)}; "
            f"stdout={stdout!r}; stderr={stderr!r}"
        )
    return result


def _assert_stock_zip(zip_path: Path, raw: bytes, *, label: str) -> None:
    if not zip_path.is_file():
        raise RuntimeError(f"{label} native ZIP export did not publish output")
    extracted = zip_path.parent / f"{label}-zip-tree"
    extracted.mkdir()
    with zipfile.ZipFile(zip_path) as zf:
        names = {item.filename for item in zf.infolist()}
        zf.extractall(extracted)
    restored = (extracted / USER_PATH).read_bytes()
    if restored != raw:
        raise RuntimeError(f"{label} stock ZIP extraction changed logical regular-file bytes")
    if "dir/" not in names or USER_PATH not in names:
        raise RuntimeError(f"{label} ZIP export omitted canonical regular/directory entries: {sorted(names)!r}")
    print(f"{label}-zip-export=PASS bytes={zip_path.stat().st_size}")


def _exercise_r24(binary: Path, root: Path, raw: bytes) -> None:
    source = root / "r24-source"
    (source / "dir").mkdir(parents=True)
    (source / USER_PATH).write_bytes(raw)
    archive = root / "r24.cmpct"
    Builder(source).build(archive)

    info = _run(binary, "info", str(archive)).stdout.decode("utf-8", errors="strict")
    if "revision=24\n" not in info:
        raise RuntimeError(f"fallback fixture is not genuine r24 according to native dispatcher: {info!r}")
    _run(binary, "verify", str(archive))
    zip_path = root / "r24.zip"
    _run(binary, "export-zip", str(archive), str(zip_path))
    _assert_stock_zip(zip_path, raw, label="r24")


def _exercise_r25(binary: Path, root: Path, raw: bytes) -> None:
    manifest, _ = _regular_manifest()
    for name, maker in (("g04", G.g04_archive), ("prefixgraph", G.prefix_archive)):
        archive_bytes, _tree = maker(manifest, raw)
        archive = root / f"{name}.cmpct"
        archive.write_bytes(archive_bytes)
        _run(binary, "verify", str(archive))

        zip_path = root / f"{name}.zip"
        _run(binary, "export-zip", str(archive), str(zip_path))
        _assert_stock_zip(zip_path, raw, label=name)


def _exercise_atomic_failure(binary: Path, root: Path) -> None:
    # The independent canonical fixture includes hardlink/symlink semantics that stock ZIP cannot represent under
    # the selected honest export policy. The exporter is allowed to discover this only after serializing earlier
    # entries, so it is a useful hostile test of public-path publication rather than merely an upfront rejection.
    manifest, fs = G.filesystem_payload()
    archive_bytes, _tree = G.g04_archive(manifest, fs["raw"])
    archive = root / "unsupported-links.cmpct"
    archive.write_bytes(archive_bytes)
    _run(binary, "verify", str(archive))

    destination = root / "existing.zip"
    sentinel = b"CMPCT-ZIP-ATOMIC-SENTINEL\n"
    destination.write_bytes(sentinel)
    result = _run(binary, "export-zip", str(archive), str(destination), check=False)
    if result.returncode == 0:
        raise RuntimeError("ZIP export silently accepted filesystem semantics that the stock projection cannot preserve")
    if destination.read_bytes() != sentinel:
        raise RuntimeError("failed ZIP export changed or replaced the pre-existing public destination")
    leftovers = sorted(
        path.name
        for path in root.iterdir()
        if path.name.startswith(".existing.zip.cmpct-zip-")
    )
    if leftovers:
        raise RuntimeError(f"failed ZIP export leaked transactional stage/backup files: {leftovers!r}")
    print("zip-atomic-failure=PASS")


def run(binary: Path) -> None:
    binary = Path(binary)
    if not binary.is_file():
        raise RuntimeError(f"native portable binary missing: {binary}")
    _manifest, raw = _regular_manifest()
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-zip-") as td:
        root = Path(td)
        _exercise_r24(binary, root, raw)
        _exercise_r25(binary, root, raw)
        _exercise_atomic_failure(binary, root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    args = parser.parse_args()
    run(args.binary)

# Footnote: ordinary ZIP cannot represent CMPCT's full symlink/xattr/recovery contract portably, so successful
# stock-ZIP parity uses a regular-file/directory tree. The independent canonical link fixture instead proves the
# typed unsupported path is transactional: a late semantic rejection may never replace a valid pre-existing public
# destination or leak staging files. Genuine r24 fallback plus both publishable r25 profile families are exercised
# through the same shared native dispatcher; no profile receives inferred ZIP credit from another representation.
