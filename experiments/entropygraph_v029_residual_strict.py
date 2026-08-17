"""Stable evidence wrapper for CMPCT attempt #5 Residual Program Packing.

The older ``entropygraph_v029_mosaic_strict.py`` remains pinned to attempt #4 and is therefore a safe,
immutable parent for the post-placement compiler.  This separate wrapper exposes attempt #5 to tests and
benchmarks without creating a circular import or rewriting the attempt-4 evidence boundary.

Footnote: keeping one strict wrapper per measured mechanism makes failure history reproducible.  An
attempt-5 red can be investigated without silently changing the executable entry point that produced the
preserved attempt-4 result.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
IMPL_PATH = HERE / "entropygraph_v029_residual_pack.py"


def _load_impl():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v029_residual_pack_strict", IMPL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load attempt-5 Residual Program Packing engine")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


IMPL = _load_impl()
BASE = IMPL.P
MAG = IMPL.MAG
PLACEMENT_MAG = IMPL.P.MAG
HDR = IMPL.HDR
FTR = IMPL.FTR
PH = IMPL.PH
MAX_READ_AMP = IMPL.MAX_READ_AMP
MAX_RESIDUAL_PACK = IMPL.MAX_RESIDUAL_PACK
MAX_ADDITIONAL_RECIPE_AMP = IMPL.MAX_ADDITIONAL_RECIPE_AMP


def build(root: Path, out: Path) -> dict:
    return IMPL.build(root, out)


def build_graph(root: Path, out: Path) -> dict:
    return IMPL.build_graph(root, out)


def extract(archive: Path, dst: Path) -> None:
    IMPL.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    return IMPL.strong_verify(archive)


def bench(root: Path, out: Path) -> dict:
    return IMPL.bench(root, out)


def _open(archive: Path):
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic == MAG:
        return IMPL._open(archive)
    if magic == PLACEMENT_MAG:
        return IMPL.A4._open(archive)
    raise RuntimeError("research graph is neither CMPNX10 placement nor CMPNX11 residual-pack")


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT strict attempt-5 Residual Program Packing engine")
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
