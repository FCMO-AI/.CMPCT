"""Strict-baseline reconciliation wrapper for CMPCT attempt #5.

Attempt #5 passed its originally encoded archive gate, but post-pass audit found that the experiment
lineage still referenced the historical pre-strict ``entropygraph_v028.py`` module.  On
``05_compressed_stream_avalan`` that allowed an ordinary root pack with ~23.68x selective-read
amplification even though released v0.28 had already frozen an <=8x pack-locality contract.

This wrapper deliberately changes no Mosaic Placement or Residual Program Packing mechanism.  It patches
only the inherited v0.28 policy hooks on the already-loaded shared module object:

* portfolio build/extract/strong-verify delegate to ``entropygraph_v028_strict.py``;
* root-pack selection delegates to ``strict_choose_pack_plan`` (which includes the always-feasible 1x
  independent-record floor and accepts only <=8x plans).

Because the placement/residual modules hold references to that same v0.28 module object, the policy repair
applies to both the outer baseline and every internal root-pack tournament without duplicating graph code.

Footnote: attempt #5's original executable and evidence remain untouched.  This file is a reconciliation
surface so the mechanism must re-earn its full-artifact result under the actual released v0.28 contract;
a regression is evidence, not permission to weaken the 8x bound.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ATTEMPT5_PATH = HERE / "entropygraph_v029_residual_strict.py"
STRICT_V028_PATH = HERE / "entropygraph_v028_strict.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ATTEMPT5 = _load(ATTEMPT5_PATH, "cmpct_v029_attempt5_for_strict_reconcile")
STRICT_V028 = _load(STRICT_V028_PATH, "cmpct_v028_strict_for_v029_reconcile")

# The attempt-5 chain shares one historical v0.28 module object through Placement Compiler -> attempt #3
# -> attempt #2 -> attempt #1.  Patch the policy functions on that object rather than swapping module
# identities; this preserves helper attributes (_preflate_pack, _merkle_root, codecs, constants) that the
# research graph already calls while ensuring every pack tournament and outer baseline uses released
# strict policy.
LEGACY_V028 = ATTEMPT5.IMPL.V028
LEGACY_V028._choose_pack_plan = STRICT_V028.strict_choose_pack_plan
LEGACY_V028.build = STRICT_V028.build
LEGACY_V028.extract = STRICT_V028.extract
LEGACY_V028.strong_verify = STRICT_V028.strong_verify

# Defensive invariant: placement and residual modules must point to the same patched object. If a future
# refactor forks those references, fail loudly instead of silently applying strictness to only one layer.
if ATTEMPT5.IMPL.P.V028 is not LEGACY_V028:
    raise RuntimeError("attempt-5 placement and residual v0.28 references diverged")

IMPL = ATTEMPT5.IMPL
BASE = ATTEMPT5.BASE
MAG = ATTEMPT5.MAG
PLACEMENT_MAG = ATTEMPT5.PLACEMENT_MAG
HDR = ATTEMPT5.HDR
FTR = ATTEMPT5.FTR
PH = ATTEMPT5.PH
MAX_READ_AMP = ATTEMPT5.MAX_READ_AMP
MAX_RESIDUAL_PACK = ATTEMPT5.MAX_RESIDUAL_PACK
MAX_ADDITIONAL_RECIPE_AMP = ATTEMPT5.MAX_ADDITIONAL_RECIPE_AMP


def build(root: Path, out: Path) -> dict:
    result = ATTEMPT5.build(root, out)
    pack_amp = float(result["mosaic"].get("pack_read_amplification", 0.0))
    if result["selected"] == "mosaic" and pack_amp > STRICT_V028.READ_AMPLIFICATION_BUDGET:
        raise RuntimeError(
            f"strict-reconciled attempt #5 selected ordinary pack amplification {pack_amp:.6f}x > "
            f"{STRICT_V028.READ_AMPLIFICATION_BUDGET:.1f}x"
        )
    result["strict_v028_reconciled"] = True
    result["ordinary_pack_read_amplification_budget"] = STRICT_V028.READ_AMPLIFICATION_BUDGET
    return result


def build_graph(root: Path, out: Path) -> dict:
    stats = ATTEMPT5.build_graph(root, out)
    pack_amp = float(stats.get("pack_read_amplification", 0.0))
    if pack_amp > STRICT_V028.READ_AMPLIFICATION_BUDGET:
        raise RuntimeError(
            f"strict-reconciled research graph ordinary pack amplification {pack_amp:.6f}x > "
            f"{STRICT_V028.READ_AMPLIFICATION_BUDGET:.1f}x"
        )
    stats["strict_v028_reconciled"] = True
    stats["ordinary_pack_read_amplification_budget"] = STRICT_V028.READ_AMPLIFICATION_BUDGET
    return stats


def extract(archive: Path, dst: Path) -> None:
    ATTEMPT5.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    return ATTEMPT5.strong_verify(archive)


def bench(root: Path, out: Path) -> dict:
    result = build(root, out)
    # Keep attempt #5's verification behavior but avoid calling its build() a second time.
    import statistics
    import time
    samples = []
    for _ in range(3):
        started = time.perf_counter()
        strong_verify(out)
        samples.append(time.perf_counter() - started)
    result["strong_verify_median_s"] = statistics.median(samples)
    result["tree_sha256"] = BASE.treehash(root)
    return result


def _open(archive: Path):
    return ATTEMPT5._open(archive)


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT attempt-5 strict-v0.28 reconciliation wrapper")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    p = sub.add_parser("extract"); p.add_argument("archive", type=Path); p.add_argument("destination", type=Path)
    p = sub.add_parser("verify"); p.add_argument("archive", type=Path)
    p = sub.add_parser("bench"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.cmd == "pack":
        print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    elif args.cmd == "extract":
        extract(args.archive, args.destination)
        print(json.dumps({"ok": True}, indent=2))
    elif args.cmd == "verify":
        print(json.dumps(strong_verify(args.archive), indent=2, default=str))
    else:
        print(json.dumps(bench(args.source, args.archive), indent=2, default=str))


if __name__ == "__main__":
    _main()
