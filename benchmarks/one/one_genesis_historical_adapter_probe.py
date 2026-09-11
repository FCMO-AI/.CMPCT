from __future__ import annotations

"""Pre-gate probe for input-pure frozen CMPCT comparator surfaces.

The Genesis executor owns the physical workload trees.  Historical generalization harnesses
are therefore not valid adapters because they regenerate their own corpora.  This probe loads
only the frozen product/compressor front door, gives it an externally-created transfer tree,
and checks build -> strong_verify -> extract exactness.

It is intentionally not a Genesis measurement adapter: it never touches the frozen 15-workload
matrix, never compares contenders, and never emits a winner.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

V029_SHA = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
V030_SHA = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
SURFACES = {
    "v0.29": (V029_SHA, "experiments/entropygraph_v029_residual_strict.py"),
    "v0.30": (V030_SHA, "experiments/entropygraph_v030_release_product.py"),
}
CORPUS_MODULE_MARKERS = (
    "neutral_hostile_corpus_v1",
    "resemblance_hostile_corpus_v1",
    "neutral_hostile_determinism_repair",
)


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(rel).to_bytes(4, "little"))
        digest.update(rel)
        digest.update(len(data).to_bytes(8, "little"))
        digest.update(data)
    return digest.hexdigest()


def _write_transfer_tree(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=False)
    (root / "nested").mkdir()
    (root / "alpha.txt").write_bytes((b"law-surprise-transfer-probe\n" * 257) + bytes(range(64)))
    (root / "nested" / "beta.bin").write_bytes(bytes((i * 73 + 19) & 0xFF for i in range(8192)))
    (root / "nested" / "empty").write_bytes(b"")


def _module_from_path(checkout: Path, relpath: str, name: str):
    path = checkout / relpath
    if not path.is_file():
        raise RuntimeError(f"frozen comparator surface missing: {path}")
    sys.path.insert(0, str(checkout))
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load frozen comparator surface: {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if sys.path and sys.path[0] == str(checkout):
            sys.path.pop(0)


def _historical_corpus_modules_loaded() -> list[str]:
    return sorted(
        name for name in sys.modules
        if any(marker in name for marker in CORPUS_MODULE_MARKERS)
    )


def probe(contender: str, checkout: Path) -> dict[str, Any]:
    if contender not in SURFACES:
        raise RuntimeError(f"unsupported frozen contender: {contender!r}")
    expected_sha, relpath = SURFACES[contender]
    checkout = checkout.resolve()
    observed_sha = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if observed_sha != expected_sha:
        raise RuntimeError(f"{contender}: checkout HEAD {observed_sha} != frozen {expected_sha}")

    before_corpus_modules = set(_historical_corpus_modules_loaded())
    module = _module_from_path(checkout, relpath, f"cmpct_one_genesis_probe_{contender.replace('.', '_')}")
    for required in ("build", "strong_verify", "extract"):
        if not callable(getattr(module, required, None)):
            raise RuntimeError(f"{contender}: frozen surface lacks callable {required}()")

    with tempfile.TemporaryDirectory(prefix=f"cmpct-one-{contender}-adapter-probe-") as td:
        base = Path(td)
        source = base / "external-input"
        archive = base / "probe.cmpct"
        extracted = base / "extracted"
        _write_transfer_tree(source)
        source_digest = _tree_digest(source)

        cpu0 = time.process_time()
        wall0 = time.perf_counter()
        stats = module.build(source, archive)
        build_cpu_s = time.process_time() - cpu0
        build_wall_s = time.perf_counter() - wall0
        if not archive.is_file():
            raise RuntimeError(f"{contender}: build did not create archive")

        verified = module.strong_verify(archive)
        if not isinstance(verified, dict) or verified.get("ok") is not True:
            raise RuntimeError(f"{contender}: strong_verify failed: {verified!r}")

        module.extract(archive, extracted)
        extracted_digest = _tree_digest(extracted)
        if extracted_digest != source_digest:
            raise RuntimeError(f"{contender}: extracted transfer tree differs from external input")

        archive_bytes = archive.stat().st_size
        selected = stats.get("selected") if isinstance(stats, dict) else None

    after_corpus_modules = set(_historical_corpus_modules_loaded())
    newly_loaded_corpus_modules = sorted(after_corpus_modules - before_corpus_modules)
    if newly_loaded_corpus_modules:
        raise RuntimeError(
            f"{contender}: direct product surface unexpectedly loaded historical corpus modules: "
            f"{newly_loaded_corpus_modules}"
        )

    return {
        "schema": "cmpct-one-genesis-historical-adapter-probe-v1",
        "claim_boundary": "synthetic transfer-tree build/verify/extract compatibility only; no Genesis workload measurement or scoring",
        "contender": contender,
        "source_sha": expected_sha,
        "surface": relpath,
        "external_input_owned_by_probe": True,
        "historical_generalization_harness_invoked": False,
        "historical_corpus_modules_newly_loaded": newly_loaded_corpus_modules,
        "build_verify_extract_exact": True,
        "archive_bytes_diagnostic_only": archive_bytes,
        "build_cpu_s_diagnostic_only": build_cpu_s,
        "build_wall_s_diagnostic_only": build_wall_s,
        "selected_diagnostic_only": selected,
        "genesis_15_workloads_touched": False,
        "comparisons_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contender", choices=sorted(SURFACES), required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.contender, args.checkout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
