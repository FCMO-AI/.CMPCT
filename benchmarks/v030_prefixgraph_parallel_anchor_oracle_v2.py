from __future__ import annotations

"""Repair wrapper for the exact-byte PrefixGraph parallel-anchor oracle.

The v1 oracle asked for logical target names (``shifted_versions`` and
``boundary_churn``), while the frozen hostile corpus deliberately prefixes its
on-disk directories with ordering numbers (``01_`` / ``03_``).  That mismatch
made the experiment die before either scheduling implementation ran.

This wrapper changes only target discovery.  It delegates corpus generation,
serial/parallel builders, exact-byte tournament, strong verification, locality,
and the frozen >=20% + >=1s materiality hurdle back to v1 unchanged.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_prefixgraph_parallel_anchor_oracle as V1
from benchmarks import v030_prefixgraph_terminal_parity_oracle as TERM


def _logical_target(name: str) -> str | None:
    for target in V1.TARGETS:
        if name == target or name.endswith("_" + target):
            return target
    return None


def _find_targets(work_root: Path) -> list[tuple[str, Path]]:
    _accepted, roots = TERM._corpora(work_root)
    found: dict[str, tuple[str, Path]] = {}
    for suite, root in roots:
        for source in sorted(path for path in root.iterdir() if path.is_dir()):
            key = _logical_target(source.name)
            if key is not None:
                if key in found:
                    raise RuntimeError(f"duplicate frozen PrefixGraph target for {key}: {source}")
                found[key] = (suite, source)
    missing = sorted(V1.TARGETS - found.keys())
    if missing:
        raise RuntimeError(f"missing frozen PrefixGraph target workloads after logical-name normalization: {missing}")
    return [found[name] for name in sorted(V1.TARGETS)]


def run(work_root: Path) -> dict:
    original = V1._find_targets
    V1._find_targets = _find_targets
    try:
        result = dict(V1.run(work_root))
    finally:
        V1._find_targets = original
    result["schema"] = "cmpct-v030-prefixgraph-parallel-anchor-v2"
    result["target_discovery"] = {
        "type": "logical-name-normalization-only",
        "frozen_corpus_directory_prefixes_accepted": True,
        "builder_or_tournament_changed": False,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-parallel-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-parallel.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": result["rows"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("PrefixGraph parallel anchor scheduling did not earn promotion")


if __name__ == "__main__":
    main()
