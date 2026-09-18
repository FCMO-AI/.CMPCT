from __future__ import annotations

"""Research-only oracle: does proven v0.25 Office ZIP-stream value survive r25 filesystem framing?"""

import importlib.util
import json
from pathlib import Path
import tempfile

from experiments import entropygraph_v030_canonical_final_impl as final

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TREE = "aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57"
EXPECTED_LOGICAL = 16_063_798
EXPECTED_FILES = 20


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_v025(mod, root: Path, out: Path) -> dict:
    mod.ROOT = root
    mod.OUT = out
    build = mod.build()
    verify = mod.strong_verify()
    if not verify.get("ok"):
        raise RuntimeError(f"v0.25 exact verification failed: {verify}")
    return {"archive_bytes": out.stat().st_size, "build": build, "strong_verify": verify}


def main() -> None:
    neutral = load(ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_neutral_office_r25_framing")
    repair = load(ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v6.py", "cmpct_repair_office_r25_framing")
    control = load(ROOT / "experiments" / "entropygraph_v025.py", "cmpct_v025_office_r25_framing_control")
    framed = load(ROOT / "experiments" / "entropygraph_v025.py", "cmpct_v025_office_r25_framing_framed")

    with tempfile.TemporaryDirectory(prefix="cmpct-office-v025-r25-framing-") as td:
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

        c = run_v025(control, office, work / "control.cmpct")

        staging = work / "r25-staging"
        with final._revision25_profile_context():
            prepared = final._prepare_profile_tree(office, staging)
        f = run_v025(framed, staging, work / "framed.cmpct")
        selected_manifest = bytes(prepared["selected_manifest_raw"])
        source_manifest = bytes(prepared["source_manifest_raw"])
        delta = f["archive_bytes"] - c["archive_bytes"]
        result = {
            "schema": "cmpct-v030-office-v025-r25-framing-oracle-v1",
            "release_credit": False,
            "claim_boundary": "research-only oracle: checked-in v0.25 representation on current canonical r25 prepared-tree/control semantics; no locality/product/release credit",
            "substrate": "neutral-hostile-determinism-repair-v6",
            "office_tree_sha256": tree,
            "logical_bytes": logical,
            "files": len(files),
            "control_v025": c,
            "r25_prepared_tree": {
                "entries": int(prepared["entries"]),
                "selected_manifest_encoding": prepared["selected_manifest_encoding"],
                "filesystem_v1_manifest_bytes": len(source_manifest),
                "selected_manifest_bytes": len(selected_manifest),
                "manifest_control_saving_bytes": int(prepared["manifest_control_saving_bytes"]),
                "staged_files": sum(1 for p in staging.rglob("*") if p.is_file()),
                "tree_sha256": framed.treehash(staging),
            },
            "v025_on_r25_prepared_tree": f,
            "r25_framing_minus_original_v025_bytes": delta,
            "r25_framing_overhead_pct_of_original_v025": (100.0 * delta / c["archive_bytes"]) if c["archive_bytes"] else 0.0,
            "decision": "R25_FRAMING_PRESERVES_ZIPSTREAM_HEADROOM" if delta < 1_000_000 else "R25_FRAMING_COST_MATERIAL_REQUIRES_ATTRIBUTION",
        }
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
