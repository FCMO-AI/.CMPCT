from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
NEUTRAL_PATH = ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py"
REPAIR_PATH = ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v6.py"
ACCEPTED_PATH = ROOT / "benchmarks" / "history" / "2026-08-19-neutral-hostile-determinism-repair-v6.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_repair_v6_aggregate_developer_matches_accepted_direct_producer(tmp_path: Path) -> None:
    neutral = _load(NEUTRAL_PATH, "cmpct_test_repair_v6_aggregate_neutral")
    repair = _load(REPAIR_PATH, "cmpct_test_repair_v6_aggregate_repair")
    repair.install_generation_hooks(neutral)

    direct_root = tmp_path / "direct"
    direct_root.mkdir()
    neutral.corpus_source_repo(direct_root)
    direct_workload = direct_root / repair.DEVELOPER_NAME
    direct_tree = neutral.tree_hash(direct_workload)

    # Keep this regression focused and fast: aggregate build semantics are exercised with every sibling producer
    # replaced by a no-op. The historical build still constructs its runtime builder table and MANIFEST.json,
    # while repair-v6 must make its developer path identical to the separately accepted producer path.
    for name in (
        "corpus_office",
        "corpus_media",
        "corpus_analytics",
        "corpus_logs",
        "corpus_backups",
        "corpus_incompressible",
        "corpus_tinyfiles",
        "corpus_ml",
        "corpus_disk",
    ):
        setattr(neutral, name, lambda _root: None)

    aggregate_root = tmp_path / "aggregate"
    manifest = neutral.build(aggregate_root)
    aggregate_workload = aggregate_root / repair.DEVELOPER_NAME
    aggregate_tree = neutral.tree_hash(aggregate_workload)

    accepted = json.loads(ACCEPTED_PATH.read_text(encoding="utf-8"))
    accepted_row = next(row for row in accepted["rows"] if row["name"] == repair.DEVELOPER_NAME)
    assert direct_tree == accepted_row["tree_sha256"]
    assert aggregate_tree == direct_tree

    row = next(item for item in manifest["corpora"] if item["name"] == repair.DEVELOPER_NAME)
    assert row["tree_sha256"] == direct_tree
    assert row["files"] == accepted_row["files"]
    assert row["logical_bytes"] == accepted_row["logical_bytes"]

    persisted = json.loads((aggregate_root / "MANIFEST.json").read_text(encoding="utf-8"))
    persisted_row = next(item for item in persisted["corpora"] if item["name"] == repair.DEVELOPER_NAME)
    assert persisted_row == row
