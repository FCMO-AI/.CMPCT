from __future__ import annotations

"""Full-build A/B for the proven Office lazy ZIP plaintext prefilter.

The focused oracle proved size+CRC32 can eliminate 158/178 member inflations without changing any exact SHA-256
cross-representation edge. This oracle asks the productization question: with only that patch applied to the actual
EntropyGraph engine, are complete graph archives byte-identical and is the end-to-end build materially faster?
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_federated_compact_framing_v8_policy_distill as V1

ROUNDS = 7
MIN_ABSOLUTE_SAVING_S = 0.020


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load engine module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _one(mod, source: Path, output: Path) -> tuple[float, bytes, dict]:
    mod.ROOT = source
    mod.OUT = output
    started = time.perf_counter()
    info = mod.build()
    elapsed = time.perf_counter() - started
    raw = output.read_bytes()
    verified = mod.strong_verify()
    if not verified.get("ok"):
        raise RuntimeError("full graph build failed strong verification")
    return elapsed, raw, info


def run(work_root: Path, baseline_module: Path, candidate_module: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, accepted_v029 = V1._frozen_office(work_root / "frozen")
    baseline = _load(baseline_module, "cmpct_eg08_ab_baseline")
    candidate = _load(candidate_module, "cmpct_eg08_ab_candidate")
    samples = []
    reference_sha = None
    reference_bytes = None
    for i in range(ROUNDS):
        order = (("baseline", baseline), ("candidate", candidate)) if i % 2 == 0 else (("candidate", candidate), ("baseline", baseline))
        rows = {}
        for label, mod in order:
            elapsed, raw, info = _one(mod, source, work_root / f"{label}-{i}.cmpct")
            rows[label] = {"elapsed_s": elapsed, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "reported": info}
        if rows["baseline"]["sha256"] != rows["candidate"]["sha256"] or rows["baseline"]["bytes"] != rows["candidate"]["bytes"]:
            raise RuntimeError("lazy ZIP plaintext product candidate changed exact graph archive bytes")
        reference_sha = reference_sha or rows["baseline"]["sha256"]
        reference_bytes = reference_bytes or rows["baseline"]["bytes"]
        if rows["baseline"]["sha256"] != reference_sha or rows["baseline"]["bytes"] != reference_bytes:
            raise RuntimeError("baseline graph build is not deterministic across A/B rounds")
        samples.append({"baseline_s": rows["baseline"]["elapsed_s"], "candidate_s": rows["candidate"]["elapsed_s"]})
    baseline_median = statistics.median(row["baseline_s"] for row in samples)
    candidate_median = statistics.median(row["candidate_s"] for row in samples)
    saving = baseline_median - candidate_median
    gate = {
        "exact_archive_byte_identity": True,
        "deterministic_across_rounds": True,
        "strong_verify_each_build": True,
        "candidate_faster": candidate_median < baseline_median,
        "material_absolute_saving": saving >= MIN_ABSOLUTE_SAVING_S,
        "release_credit": False,
    }
    return {
        "schema": "cmpct-v030-eg08-lazy-zip-product-ab-v1",
        "target": "neutral_hostile_v1/03_office_documents",
        "accepted_v029_bytes": int(accepted_v029),
        "rounds": ROUNDS,
        "archive_bytes": int(reference_bytes),
        "archive_sha256": reference_sha,
        "samples": samples,
        "baseline_median_s": baseline_median,
        "candidate_median_s": candidate_median,
        "median_saving_s": saving,
        "relative_speedup": saving / max(baseline_median, 1e-12),
        "gate": {**gate, "passed": all(v is True for k, v in gate.items() if k != "release_credit")},
        "promotion_signal": all(v is True for k, v in gate.items() if k != "release_credit"),
        "release_credit": False,
        "claim_boundary": (
            "Ephemeral product-code A/B only. A pass proves the lazy size+CRC32 prefilter preserves exact graph "
            "archive bytes and materially reduces complete graph-build time. SHA-256 remains the edge admission proof. "
            "Canonical C25EG08 create timing versus ZIP/Zstd, selector, native/Android/recovery and final authority "
            "remain separate gates."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--baseline-module", type=Path, required=True)
    p.add_argument("--candidate-module", type=Path, required=True)
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-lazy-zip-product-ab-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-lazy-zip-product-ab.json"))
    a = p.parse_args()
    result = run(a.work_root, a.baseline_module, a.candidate_module)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("archive_bytes", "baseline_median_s", "candidate_median_s", "median_saving_s", "relative_speedup", "gate")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
