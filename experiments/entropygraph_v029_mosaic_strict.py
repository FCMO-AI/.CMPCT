"""Strict-locality wrapper for the CMPCT multi-root mosaic full-artifact experiment.

The first full-artifact engine records a bounded candidate-root list in each mosaic descriptor.  Its
reader materializes that entire list before decoding the opcode stream.  Therefore locality accounting
must charge **every descriptor-listed root**, not only slots that ultimately emit COPY bytes.

Rather than hiding that correction inside benchmark code, this wrapper makes the stricter semantics an
executable research engine.  It mirrors the v0.28 ``entropygraph_v028_strict`` pattern: the underlying
experiment remains inspectable, while evidence and any future promotion use the conservative contract.

Footnote: patching ``used_base_slots`` here is deliberately harsher than the primitive metric.  The
mosaic payload itself is unchanged; the wrapper simply makes admission behave as though every supplied
slot is used, which exactly matches what the current reader materializes.  A future grammar may encode a
compacted root dictionary, but it must earn that lower read cost with real bytes and reader behavior.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "entropygraph_v029_mosaic.py"


def _load_base():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v029_mosaic_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load mosaic full-artifact engine")
    module = importlib.util.module_from_spec(spec)
    # Footnote: dynamic modules are registered before execution so dataclass/type machinery in future
    # research dependencies sees a normal import environment instead of an anonymous loader object.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_base()


def _all_descriptor_slots(stats) -> tuple[int, ...]:
    return tuple(range(len(stats.copied_by_base)))


# The base engine asks this helper which candidate slots should be charged to the read-amplification
# calculation and metadata admission path.  Current reader semantics materialize all descriptor roots.
BASE.used_base_slots = _all_descriptor_slots

MAG = BASE.MAG
HDR = BASE.HDR
FTR = BASE.FTR
PH = BASE.PH
MAX_READ_AMP = BASE.MAX_READ_AMP


def build(root: Path, out: Path) -> dict:
    return BASE.build(root, out)


def build_graph(root: Path, out: Path) -> dict:
    """Build the strict mosaic graph directly, bypassing outer v0.28 fallback for conformance tests."""
    return BASE._build_mosaic_graph(root, out)


def extract(archive: Path, dst: Path) -> None:
    BASE.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    return BASE.strong_verify(archive)


def bench(root: Path, out: Path) -> dict:
    return BASE.bench(root, out)


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
