#!/usr/bin/env python3
"""Full-charge Office counterfactual for the inherited v0.25 compact floor.

Question: how much complete-artifact value is causally owned by ZIP-stream
virtualization on the accepted repair-v6 Office tree?

The control executes the checked-in v0.25 research engine unchanged. The
counterfactual executes the same source with exactly one selection predicate
instrumented so no ZIP container can enter ``special``. This deliberately keeps
all downstream generic mechanisms alive: it measures the value of admitting
ZIP-stream virtualization, not a hand-constructed replacement archive.

Research evidence only; never canonical/release credit.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TREE = "aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57"
EXPECTED_LOGICAL = 16_063_798
EXPECTED_FILES = 20
SENTINEL = "if zp['local_dup'] < 512*1024 and shared_unique < 32*1024 and external_match < 32*1024:continue"
REPLACEMENT = "if True:continue  # counterfactual: disable ZIP-stream admission"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_no_zipstreams() -> types.ModuleType:
    path = ROOT / "experiments" / "entropygraph_v025.py"
    source = path.read_text(encoding="utf-8")
    if source.count(SENTINEL) != 1:
        raise RuntimeError("v0.25 ZIP-stream admission sentinel changed; ablation fails closed")
    source = source.replace(SENTINEL, REPLACEMENT)
    mod = types.ModuleType("cmpct_v025_office_no_zipstreams")
    mod.__file__ = str(path)
    exec(compile(source, str(path), "exec"), mod.__dict__)
    return mod


def run_engine(mod, office: Path, out: Path) -> dict:
    mod.ROOT = office
    mod.OUT = out
    build = mod.build()
    verify = mod.strong_verify()
    if not verify.get("ok") or verify.get("tree_sha256") != EXPECTED_TREE:
        raise RuntimeError(f"exact verification failed for {out.name}: {verify}")
    return {
        "archive_bytes": out.stat().st_size,
        "build": build,
        "strong_verify": verify,
    }


def main() -> None:
    neutral = load(ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_neutral_office_zip_ablation")
    repair = load(ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v6.py", "cmpct_repair_office_zip_ablation")
    control = load(ROOT / "experiments" / "entropygraph_v025.py", "cmpct_v025_office_zip_control")
    ablated = load_no_zipstreams()

    with tempfile.TemporaryDirectory(prefix="cmpct-office-v025-zipstreams-ablation-") as td:
        work = Path(td)
        corpus = work / "corpus"
        repair.install_generation_hooks(neutral)
        neutral.corpus_office(corpus)
        office = corpus / "02_office_workspace"
        repair.normalize_workload(office)
        files = sorted(p for p in office.rglob("*") if p.is_file())
        logical = sum(p.stat().st_size for p in files)
        tree = control.treehash(office)
        if (tree, logical, len(files)) != (EXPECTED_TREE, EXPECTED_LOGICAL, EXPECTED_FILES):
            raise RuntimeError({"tree": tree, "logical": logical, "files": len(files)})

        c = run_engine(control, office, work / "control.cmpct")
        a = run_engine(ablated, office, work / "no-zipstreams.cmpct")
        delta = a["archive_bytes"] - c["archive_bytes"]
        result = {
            "schema": "cmpct-v030-office-v025-zipstreams-ablation-v1",
            "release_credit": False,
            "claim_boundary": "research-only complete-artifact counterfactual on accepted repair-v6 Office tree; disables only v0.25 ZIP-stream admission while leaving downstream generic mechanisms available",
            "substrate": "neutral-hostile-determinism-repair-v6",
            "office_tree_sha256": tree,
            "logical_bytes": logical,
            "files": len(files),
            "control": c,
            "no_zipstreams": a,
            "no_zipstreams_minus_control_bytes": delta,
            "zipstreams_complete_artifact_value_bytes": delta,
            "zipstreams_complete_artifact_value_pct_of_control": (100.0 * delta / c["archive_bytes"]) if c["archive_bytes"] else 0.0,
            "decision": "ZIPSTREAMS_CAUSALLY_MATERIAL" if delta >= 4096 else "ZIPSTREAMS_NOT_MATERIAL_ON_OFFICE",
        }
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
