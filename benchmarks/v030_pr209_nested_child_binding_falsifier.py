from __future__ import annotations

"""Focused zero-credit falsifier for PR #209 nested child product binding.

Run on PR #209 lineage. It compares:
1) genuine canonical r24,
2) the compact-r24 candidate policy in the current interpreter,
3) the exact shipping R24PrebuildProcess child.

If the parent compact candidate reaches the genuine-r24 floor while the shipping child
remains larger, PR #209's prior complete-product red measured the canonical child policy
across the nested fresh-process boundary rather than the candidate it intended to test.

This instrument does not change product policy or earn promotion credit.
"""

import hashlib
import json
import tempfile
from pathlib import Path

from benchmarks import neutral_hostile_corpus_v1 as N
from benchmarks import neutral_hostile_determinism_repair_v6 as REPAIR
from cmpct.builder import Builder
from experiments import entropygraph_v030_release_product as canonical
from experiments import entropygraph_v030_release_product_compact_r24 as candidate
from experiments.entropygraph_v030_r24_process_prebuild import R24PrebuildProcess

EXPECTED_TREE_SHA256 = "a823728d98e5882542645e3ab0f777894479cfb3de4dedcec14341fedbb11a05"
EXPECTED_FILES = 769
EXPECTED_LOGICAL_BYTES = 14_006_619


def tree_identity(root: Path) -> tuple[str, int, int]:
    h = hashlib.sha256()
    files = 0
    logical = 0
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        rel = p.relative_to(root).as_posix().encode()
        raw = p.read_bytes()
        h.update(len(rel).to_bytes(4, "little"))
        h.update(rel)
        h.update(len(raw).to_bytes(8, "little"))
        h.update(raw)
        files += 1
        logical += len(raw)
    return h.hexdigest(), files, logical


def measured_row(name: str, path: Path, stats: dict) -> dict:
    verify = canonical.strong_verify(path)
    if not verify.get("ok"):
        raise RuntimeError(f"{name} verification failed: {verify!r}")
    return {
        "name": name,
        "archive_bytes": path.stat().st_size,
        "archive_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "stats": stats,
    }


def run() -> dict:
    REPAIR.install_generation_hooks(N)
    with tempfile.TemporaryDirectory(prefix="cmpct-pr209-child-binding-") as raw:
        td = Path(raw)
        corpus = td / "corpus"
        corpus.mkdir()
        N.corpus_backups(corpus)
        root = corpus / "06_incremental_backups"
        REPAIR.normalize_workload(root)

        ident = tree_identity(root)
        expected = (EXPECTED_TREE_SHA256, EXPECTED_FILES, EXPECTED_LOGICAL_BYTES)
        if ident != expected:
            raise RuntimeError(f"substrate identity mismatch: {ident!r} != {expected!r}")

        genuine_path = td / "genuine-r24.cmpct"
        genuine_stats = dict(Builder(root).build(genuine_path))

        parent_candidate_path = td / "parent-compact-r24.cmpct"
        parent_candidate_stats = dict(candidate._locality_bounded_r24_build(root, parent_candidate_path))

        child_shipping_path = td / "shipping-child-r24.cmpct"
        child = R24PrebuildProcess(root, child_shipping_path)
        child.start()
        try:
            child_shipping_stats = dict(child.result())
        finally:
            child.close()

        rows = [
            measured_row("genuine_r24", genuine_path, genuine_stats),
            measured_row("parent_compact_candidate", parent_candidate_path, parent_candidate_stats),
            measured_row("shipping_nested_child", child_shipping_path, child_shipping_stats),
        ]
        by = {row["name"]: row for row in rows}
        genuine = int(by["genuine_r24"]["archive_bytes"])
        parent_delta = int(by["parent_compact_candidate"]["archive_bytes"]) - genuine
        child_delta = int(by["shipping_nested_child"]["archive_bytes"]) - genuine

        mismatch = parent_delta <= 0 and child_delta > 0
        return {
            "schema": "cmpct-pr209-nested-child-binding-falsifier-v1",
            "source_tree": {
                "sha256": ident[0],
                "files": ident[1],
                "logical_bytes": ident[2],
            },
            "rows": rows,
            "parent_candidate_delta_vs_genuine_r24_bytes": parent_delta,
            "shipping_child_delta_vs_genuine_r24_bytes": child_delta,
            "decision": (
                "NESTED_CHILD_BINDING_FALSIFIED_PR209_PRODUCT_DISPROOF"
                if mismatch
                else "NO_BINDING_MISMATCH_OBSERVED"
            ),
            "promotion_credit": False,
            "next_if_falsified": (
                "bind candidate module identity through the existing nested r24 child, "
                "then rerun unchanged global compression parity once"
            ),
        }


def main() -> None:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["decision"] != "NESTED_CHILD_BINDING_FALSIFIED_PR209_PRODUCT_DISPROOF":
        raise SystemExit("expected nested-child binding mismatch was not reproduced")


if __name__ == "__main__":
    main()
