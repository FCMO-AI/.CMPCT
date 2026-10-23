#!/usr/bin/env python3
"""Adversarial indistinguishability court for a fixed prospective BDC sample screen.

Follow-up preregistration is separate from the original prospective held-out test.
It asks whether identical sampled observations may hide different unsampled data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import tempfile
import time
from pathlib import Path

from benchmarks import v031_bdc_prospective_admission_oracle as A
from benchmarks import v031_bounded_drift_coordered_court as FROZEN
from cmpct.builder import Builder
from cmpct.reader import CMPCT

SIZE = 72 * 1024
COUNT = 6
WINDOW = A.WINDOW_BYTES
WINDOW_STARTS = (0, (SIZE - WINDOW) // 2, SIZE - WINDOW)


def _sources(root: Path, kind: str, common: bytes) -> Path:
    source = root / "source"
    source.mkdir()
    for i in range(COUNT):
        if kind == "related":
            raw = bytearray(common)
            raw[12000 + i] ^= 1  # Changed but outside all samples.
        elif kind == "camouflaged":
            raw = bytearray(random.Random(170423 + i).randbytes(SIZE))
            for offset in WINDOW_STARTS:
                raw[offset:offset + WINDOW] = common[offset:offset + WINDOW]
        else:
            raise KeyError(kind)
        (source / f"part{i:02d}.bin").write_bytes(raw)
    A._normalize(source)
    return source


def _full_court(work: Path, kind: str, common: bytes) -> tuple[dict, list[list[bytes]]]:
    src = _sources(work, kind, common)
    windows = [A._windows(p, p.stat().st_size)[0] for p in sorted(src.iterdir())]
    check = A.screen(src)
    sig = A._tree_signature(src)
    canonical = work / "r24.cmpct"
    t0 = time.perf_counter()
    Builder(src, workers=1, reproducible=False).build(canonical)
    r24_wall = time.perf_counter() - t0
    with CMPCT(canonical) as reader:
        reader.verify()
        reader.extractall(work / "r24-out", metadata=True)
    if A._tree_signature(work / "r24-out") != sig:
        raise AssertionError("genuine r24 source fidelity failed")
    manifest, regular, _ = FROZEN._capture(src)
    t0 = time.perf_counter()
    sibling, details = FROZEN._encode_sibling(manifest, regular)
    bdc_wall = time.perf_counter() - t0
    control, bdc, recovered = FROZEN._parse_sibling(sibling)
    if recovered != manifest:
        raise AssertionError("sibling manifest mismatch")
    restored_manifest = FROZEN._materialize_and_recapture(
        recovered, FROZEN._decoded_regular_map(control, bdc), work / "sibling-out")
    if restored_manifest != manifest:
        raise AssertionError("sibling filesystem fidelity failed")
    local = FROZEN._candidate_locality(control, bdc)
    if not local["passed"]:
        raise AssertionError("sibling locality failed")
    return ({"kind": kind, "screen": check, "r24_bytes": canonical.stat().st_size,
             "bdc_sibling_bytes": len(sibling), "strict_r24_margin": canonical.stat().st_size - len(sibling),
             "r24_create_wall_s": r24_wall, "bdc_create_wall_s": bdc_wall,
             "source_content_sha256": [hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in sorted(src.iterdir())],
             "sibling_sha256": hashlib.sha256(sibling).hexdigest(),
             "r24_sha256": hashlib.sha256(canonical.read_bytes()).hexdigest(),
             "bdc_locality": local, "bdc_complete": details},
            windows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    common = random.Random(90317).randbytes(SIZE)
    with tempfile.TemporaryDirectory(prefix="cmpct-bdc-observability-related-") as da, tempfile.TemporaryDirectory(prefix="cmpct-bdc-observability-decoy-") as db:
        related, wa = _full_court(Path(da), "related", common)
        camouflaged, wb = _full_court(Path(db), "camouflaged", common)
    exact_observation = wa == wb
    keys = ("eligible", "reason", "sample_bytes", "regular_count",
            "anchor_peer_ratios", "shared_peers")
    same_detector = all(related["screen"].get(k) == camouflaged["screen"].get(k) for k in keys)
    if not exact_observation or not same_detector or not related["screen"]["eligible"]:
        raise AssertionError("constructive sampling indistinguishability witness failed")
    if related["source_content_sha256"] == camouflaged["source_content_sha256"]:
        raise AssertionError("source variants unexpectedly equal")
    result = {"schema": "cmpct-v031-bdc-prospective-observation-indistinguishability-v1",
              "status": "SAMPLE_ONLY_UNABLE_TO_PROVE_FULL_RELATIONSHIP",
              "sampled_window_bytes_exactly_equal": exact_observation,
              "screen_decisions_identical": same_detector,
              "screen_admits_both": related["screen"]["eligible"],
              "related": related, "camouflaged": camouflaged,
              "causal_boundary": "sample-only predicate cannot distinguish these exact observations; full-content BDC-versus-genuine-r24 result determines storage economics",
              "product_credit": False, "release_credit": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
