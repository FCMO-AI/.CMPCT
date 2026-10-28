"""Stable strict evidence entry point for CMPCT multi-root mosaic research.

Attempt #4 is the current evidence engine:

- attempts #1–#3 remain separate executable research files and durable failed records;
- `entropygraph_v029_mosaic_placement.py` implements the preregistered Placement Compiler;
- canonical revision 24 remains untouched.

Footnote: benchmark/test paths import this wrapper rather than a numbered attempt directly. Switching the
implementation happens only after the attempt design is documented in repository history, so a CI run
cannot unknowingly measure a half-written mechanism.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
IMPL_PATH = HERE / "entropygraph_v029_mosaic_placement.py"


def _load_impl():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v029_mosaic_placement_strict", IMPL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Mosaic Placement Compiler")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


IMPL = _load_impl()

# Attempt #4's initial implementation called ``similarity_order(all_sketches, node_ids)`` as though the
# helper accepted a subset argument. The canonical helper accepts one sketch sequence and returns indices
# *within that sequence*. Adapt the call at the stable evidence boundary so the mechanism is unchanged:
# only the already-selected direct roots are ordered, then local positions are mapped back to node ids.
#
# Footnote: this is an API-contract repair, not a benchmark mechanism change. The nominated roots,
# co-pack ceiling, locality accounting and frozen full-artifact thresholds are exactly the preregistered
# attempt-4 values; the first CI run failed before any placement economics or benchmark could execute.
_ORIGINAL_SIMILARITY_ORDER = IMPL.similarity_order


def _subset_similarity_order(sketches, node_ids):
    selected = list(node_ids)
    local_order = _ORIGINAL_SIMILARITY_ORDER([sketches[node_id] for node_id in selected])
    return [selected[local_index] for local_index in local_order]


IMPL.similarity_order = _subset_similarity_order

BASE = IMPL.PARENT
MAG = IMPL.MAG
HDR = IMPL.HDR
FTR = IMPL.FTR
PH = IMPL.PH
MAX_READ_AMP = IMPL.MAX_READ_AMP
MAX_DEDICATED_COPACK = IMPL.MAX_DEDICATED_COPACK


def build(root: Path, out: Path) -> dict:
    return IMPL.build(root, out)


def build_graph(root: Path, out: Path) -> dict:
    return IMPL._build_graph(root, out)


def extract(archive: Path, dst: Path) -> None:
    IMPL.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    return IMPL.strong_verify(archive)


def bench(root: Path, out: Path) -> dict:
    return IMPL.bench(root, out)


def _open(archive: Path):
    return IMPL._open(archive)


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT strict multi-root Mosaic Placement Compiler")
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
