"""Stable strict evidence entry point for CMPCT multi-root mosaic research.

The branch preserves every full-artifact mechanism as a separate executable attempt:

- `entropygraph_v029_mosaic.py` — attempt #1, inherited-delta targets only;
- `entropygraph_v029_mosaic_leaf.py` — attempt #2, bounded direct-leaf eligibility;
- `entropygraph_v029_mosaic_packaware.py` — attempt #3, partial roots + physical pack-marginal admission.

This wrapper now points tests and benchmark evidence at attempt #3. The full-artifact acceptance gate is
unchanged; switching the implementation under a stable evidence path prevents benchmark scripts from
silently drifting to a different file while keeping failed attempts directly reproducible.

Footnote: attempt #3 reuses the same CMPNX9 reader/recovery grammar as attempts #1/#2. It changes only
candidate retention and physical admission economics; canonical revision 24 remains untouched.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
IMPL_PATH = HERE / "entropygraph_v029_mosaic_packaware.py"


def _load_impl():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v029_mosaic_packaware_strict", IMPL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load pack-aware mosaic full-artifact engine")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


IMPL = _load_impl()
# Compatibility handle used by tests/benchmarks for the shared tree-hash and authenticated CMPNX9 reader.
BASE = IMPL.PARENT

MAG = BASE.MAG
HDR = BASE.HDR
FTR = BASE.FTR
PH = BASE.PH
MAX_READ_AMP = BASE.MAX_READ_AMP


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
