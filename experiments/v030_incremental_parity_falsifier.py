from __future__ import annotations

"""Localize the incremental-backups parity failure, including process-state order effects."""

import hashlib
import json
from pathlib import Path
import tempfile

from benchmarks import neutral_hostile_corpus_v1 as N
from benchmarks import neutral_hostile_determinism_repair_v6 as REPAIR
from benchmarks import v030_release_ablation_canonical as ABLATION
from benchmarks import v030_release_generalization as GENERAL
from cmpct.builder import Builder
from experiments import entropygraph_v030_release_product as PROMOTED
from experiments import entropygraph_v030_release_product_base as BASE

EXPECTED_TREE_SHA256 = "a823728d98e5882542645e3ab0f777894479cfb3de4dedcec14341fedbb11a05"
EXPECTED_FILES = 769
EXPECTED_LOGICAL_BYTES = 14_006_619


def _tree_identity(root: Path) -> tuple[str, int, int]:
    h = hashlib.sha256(); files = 0; logical = 0
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8"); raw = path.read_bytes()
        h.update(len(rel).to_bytes(4, "little")); h.update(rel)
        h.update(len(raw).to_bytes(8, "little")); h.update(raw)
        files += 1; logical += len(raw)
    return h.hexdigest(), files, logical


def _genuine_r24(root: Path, out: Path) -> dict:
    stats = dict(Builder(root).build(out))
    return {**stats, "selected": "canonical-r24", "format_revision": 24}


def _build_row(name: str, builder, root: Path, out: Path) -> dict:
    stats = dict(builder(root, out)); verified = dict(PROMOTED.strong_verify(out))
    if not verified.get("ok"):
        raise RuntimeError(f"{name} failed strong verification: {verified!r}")
    return {
        "name": name, "archive_bytes": out.stat().st_size,
        "archive_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "selected": stats.get("selected"), "format_revision": stats.get("format_revision"),
        "terminal_r24": stats.get("terminal_r24", False),
        "r24_product_bytes": stats.get("r24_product_bytes"), "r25_product_bytes": stats.get("r25_product_bytes"),
    }


def main() -> None:
    REPAIR.install_generation_hooks(N)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-inc-parity-") as td_raw:
        td = Path(td_raw); corpus = td / "corpus"; corpus.mkdir()
        N.corpus_backups(corpus); root = corpus / "06_incremental_backups"; REPAIR.normalize_workload(root)
        tree_sha, files, logical = _tree_identity(root)
        if (tree_sha, files, logical) != (EXPECTED_TREE_SHA256, EXPECTED_FILES, EXPECTED_LOGICAL_BYTES):
            raise RuntimeError(f"incremental-backups substrate identity mismatch: sha={tree_sha} files={files} logical={logical}")

        rows = [
            _build_row("promoted_fresh", PROMOTED.build, root, td / "promoted-fresh.cmpct"),
            _build_row("mature_base_fresh", BASE.build, root, td / "base-fresh.cmpct"),
            _build_row("genuine_r24", _genuine_r24, root, td / "r24.cmpct"),
        ]
        r24 = int(rows[-1]["archive_bytes"])
        for row in rows: row["delta_vs_r24_bytes"] = int(row["archive_bytes"]) - r24

        # The authoritative release harness runs every historical ablation before canonical product parity in the
        # same Python process. A fresh isolated build no longer reproduces the red release row, so charge the
        # cheapest order-effect falsifier: run this workload's historical arm, then rebuild the same product row.
        expected = GENERAL._accepted_v029_rows()[("neutral_hostile_v1", "06_incremental_backups")]
        historical = ABLATION._historical_row("neutral_hostile_v1", root, expected, td / "historical")
        after = _build_row("promoted_after_same_row_historical", PROMOTED.build, root, td / "promoted-after.cmpct")
        after["delta_vs_r24_bytes"] = int(after["archive_bytes"]) - r24
        rows.append(after)

        fresh_delta = int(rows[0]["delta_vs_r24_bytes"]); base_delta = int(rows[1]["delta_vs_r24_bytes"])
        after_delta = int(after["delta_vs_r24_bytes"])
        if fresh_delta > 0 and base_delta <= 0: decision = "PROMOTED_FRONTDOOR_SHORTCUT_CAUSAL"
        elif fresh_delta > 0 and base_delta > 0: decision = "REGRESSION_BELOW_PROMOTED_SHORTCUT"
        elif fresh_delta <= 0 and after_delta > 0: decision = "SAME_ROW_HISTORICAL_STATE_CONTAMINATION_REPRODUCED"
        elif fresh_delta <= 0 and after_delta <= 0: decision = "REGRESSION_REQUIRES_BROADER_PRIOR_STATE_OR_PROVENANCE"
        else: decision = "AMBIGUOUS"

        print(json.dumps({
            "schema": "cmpct-v030-incremental-parity-falsifier-v2",
            "source_tree": {"sha256": tree_sha, "files": files, "logical_bytes": logical},
            "comparator_contract": "benchmarks/v030_release_ablation_canonical.py::_product_row ordinary Builder(root).build",
            "historical_same_row": {
                "v029_bytes": historical["variants"]["v029"]["archive_bytes"],
                "combined_bytes": historical["variants"]["combined"]["archive_bytes"],
            },
            "rows": rows, "decision": decision,
        }, indent=2, sort_keys=True))


if __name__ == "__main__": main()
