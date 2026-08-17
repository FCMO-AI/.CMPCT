"""Strict evidence wrapper for the second CMPCT multi-root mosaic full-artifact experiment.

Attempt #1 used this wrapper to compensate for descriptors that listed more roots than COPY opcodes
actually needed.  Attempt #2 fixes that mismatch in the representation itself: mosaic payloads are
re-encoded until the descriptor contains only roots that are genuinely referenced, and locality then
charges every descriptor root exactly as the reader materializes it.

This wrapper now points the benchmark/conformance surface at ``entropygraph_v029_mosaic_leaf.py`` while
leaving attempt #1 intact for reproducibility.  The wrapper remains useful as the stable evidence entry
point so benchmark scripts and tests do not quietly switch experimental engines by importing a new file.

Footnote: no threshold or canonical-format behavior changes here. The preregistered full-artifact gate
continues to compare the strict evidence entry point against complete v0.28 artifacts.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
IMPL_PATH = HERE / "entropygraph_v029_mosaic_leaf.py"


def _load_impl():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v029_mosaic_leaf_strict", IMPL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load leaf-mosaic full-artifact engine")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


IMPL = _load_impl()
# Compatibility handle used by the research tests/benchmarks for the inherited tree-hash and raw reader
# oracle. It points at attempt #1's complete reader, which attempt #2 deliberately reuses unchanged.
BASE = IMPL.PARENT

MAG = BASE.MAG
HDR = BASE.HDR
FTR = BASE.FTR
PH = BASE.PH
MAX_READ_AMP = BASE.MAX_READ_AMP


def build(root: Path, out: Path) -> dict:
    return IMPL.build(root, out)


def build_graph(root: Path, out: Path) -> dict:
    """Build attempt #2 CMPNX9 directly, bypassing outer v0.28 fallback for conformance tests."""
    return IMPL.build_graph(root, out)


def extract(archive: Path, dst: Path) -> None:
    IMPL.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    return IMPL.strong_verify(archive)


def bench(root: Path, out: Path) -> dict:
    return IMPL.bench(root, out)


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT strict multi-root mosaic full-artifact engine")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    p = sub.add_parser("extract"); p.add_argument("archive", type=Path); p.add_argument("destination", type=Path)
    p = sub.add_parser("verify"); p.add_argument("archive", type=Path)
    p = sub.add_parser("bench"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.cmd == "pack":
        print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    elif args.cmd == "extract":
        extract(args.archive, args.destination); print(json.dumps({"ok": True}, indent=2))
    elif args.cmd == "verify":
        print(json.dumps(strong_verify(args.archive), indent=2, default=str))
    else:
        print(json.dumps(bench(args.source, args.archive), indent=2, default=str))


if __name__ == "__main__":
    _main()
