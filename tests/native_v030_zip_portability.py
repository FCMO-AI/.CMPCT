#!/usr/bin/env python3
"""Canonical revision-25 ZIP/export interoperability on a fidelity-compatible user tree."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile
import zipfile

from tests import generate_v030_canonical_goldens as G


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
                ["dir/payload.bin", "f", 0o640, 1_700_000_000_100_000_002, 1000, 1000, [], [len(raw), digest]],
            ],
        }
    )
    return manifest, raw


def _run(binary: Path, *args: str, check: bool = True):
    return subprocess.run([str(binary), *args], check=check, capture_output=True)


def run(binary: Path) -> None:
    binary = Path(binary)
    manifest, raw = _regular_manifest()
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-zip-") as td:
        root = Path(td)
        for name, maker in (("g04", G.g04_archive), ("prefixgraph", G.prefix_archive)):
            archive_bytes, _tree = maker(manifest, raw)
            archive = root / f"{name}.cmpct"
            archive.write_bytes(archive_bytes)
            _run(binary, "verify", str(archive))

            zip_path = root / f"{name}.zip"
            _run(binary, "export-zip", str(archive), str(zip_path))
            if not zip_path.is_file():
                raise RuntimeError(f"{name} native ZIP export did not publish output")
            extracted = root / f"{name}-zip-tree"
            extracted.mkdir()
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extracted)
            restored = (extracted / "dir/payload.bin").read_bytes()
            if restored != raw:
                raise RuntimeError(f"{name} stock ZIP extraction changed logical regular-file bytes")
            names = {item.filename for item in zipfile.ZipFile(zip_path).infolist()}
            if "dir/" not in names or "dir/payload.bin" not in names:
                raise RuntimeError(f"{name} ZIP export omitted canonical regular/directory entries: {sorted(names)!r}")
            print(f"{name}-zip-export=PASS bytes={zip_path.stat().st_size}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    args = parser.parse_args()
    run(args.binary)

# Footnote: ordinary ZIP cannot represent CMPCT's full symlink/xattr/recovery contract portably, so this receipt
# uses a regular-file/directory tree where semantic parity is honest. The separate canonical golden test proves
# richer r25 link metadata is preserved by CMPCT itself and that native ZIP export refuses rather than lies when
# the selected tree contains unsupported link semantics.
