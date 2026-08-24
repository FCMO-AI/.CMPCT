from __future__ import annotations

"""All-15 repaired-corpus binding for the r24 compact-control composition proof.

The v1 composition oracle accidentally reused ``v030_release_performance._build_corpora``.  That helper is
intentionally a three-row runtime gate, so the composition campaign stopped after shifted versions, logs and ML
instead of exercising the frozen 15-workload release corpus.  This wrapper changes only corpus construction: it
reuses the authoritative generalization gate's accepted-v0.29 identities, repair-v6 generation hooks and both
frozen workload suites, then delegates every archive/competitor/control calculation back to the v1 oracle.

No product byte, threshold, timing boundary or admission rule changes here.
"""

from pathlib import Path

from benchmarks import v030_r24_compact_control_composition_oracle as BASE
from benchmarks import v030_release_generalization as GENERAL


def _build_all(root: Path) -> dict[str, Path]:
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_compact_control_composition_neutral_v2",
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_compact_control_composition_hostile_v2",
    )
    repair = GENERAL.V029._load(
        GENERAL.V029.REPAIR_PATH,
        "cmpct_v030_compact_control_composition_repair_v2",
    )
    repair.install_generation_hooks(neutral)

    roots: dict[str, Path] = {}
    seen_keys: set[tuple[str, str]] = set()
    for label, builder, suite_root in (
        ("neutral_hostile_v1", neutral, root / "neutral"),
        ("resemblance_hostile_v1", hostile, root / "resemblance"),
    ):
        builder.build(suite_root)
        if label == "neutral_hostile_v1":
            repair.normalize_root(suite_root)
        for workload in sorted(path for path in suite_root.iterdir() if path.is_dir()):
            key = (label, workload.name)
            expected = accepted.get(key)
            if expected is None:
                raise RuntimeError(f"unexpected frozen workload in compact-control corpus: {key!r}")
            got_tree = GENERAL._historical_treehash(workload)
            expected_tree = str(expected["tree_sha256"])
            if got_tree != expected_tree:
                raise RuntimeError(
                    f"compact-control frozen source drift for {label}/{workload.name}: "
                    f"{got_tree} != {expected_tree}"
                )
            if workload.name in roots:
                raise RuntimeError(f"compact-control workload basename collision: {workload.name!r}")
            roots[workload.name] = workload
            seen_keys.add(key)

    missing = sorted(set(accepted) - seen_keys)
    if missing or len(roots) != 15:
        raise RuntimeError(
            f"compact-control composition requires the exact 15 accepted workloads: "
            f"built={len(roots)} missing={missing!r}"
        )
    return roots


BASE._build_all = _build_all


if __name__ == "__main__":
    BASE.main()
