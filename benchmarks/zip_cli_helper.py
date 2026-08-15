#!/usr/bin/env python3
from __future__ import annotations

"""Minimal fresh-process ZIP helper used only by the parity benchmark.

Footnote: keep this module free of CMPCT imports. The CLI parity layer is meant to charge each side
for its own real interpreter/import startup, not make ZIP import CMPCT merely because the benchmark
orchestrator happens to know about both formats.
"""

import argparse
import shutil
import zipfile
from pathlib import Path


def create(src: Path, out: Path) -> None:
    try:
        out.unlink()
    except FileNotFoundError:
        pass
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zf:
        for p in sorted(src.rglob("*")):
            rel = p.relative_to(src).as_posix()
            if p.is_dir():
                continue
            zf.write(p, rel)


def extract(archive: Path, dest: Path) -> None:
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir()
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("create", "extract"))
    parser.add_argument("source")
    parser.add_argument("destination")
    ns = parser.parse_args()
    if ns.operation == "create":
        create(Path(ns.source), Path(ns.destination))
    else:
        extract(Path(ns.source), Path(ns.destination))


if __name__ == "__main__":
    main()
