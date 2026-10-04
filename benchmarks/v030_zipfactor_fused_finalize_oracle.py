from __future__ import annotations

"""Same-runner exact-byte A/B for the final ZIP-factor V3 Python builder gap.

The current in-process Rust verifier is already ~0.36 ms median; the complete frontier remains ~0.18 ms slower
than ZIP because the Python builder dominates.  This oracle compares the existing V3 builder against a fused
finalization implementation that must emit byte-identical CMP25Z3 archives.  It grants no release/selector credit.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_zipfactor_compact_v3 as BASE
from experiments import entropygraph_v030_zipfactor_compact_v3_fused_finalize as FUSED

ROUNDS = 15
LEVEL = 3
GROUP_SIZE = 7
MIN_RELATIVE_SPEEDUP = 0.02
MIN_ABSOLUTE_SPEEDUP_S = 0.00010


def _timed(builder, stage: Path, archive: Path) -> float:
    started = time.perf_counter()
    builder(stage, archive, level=LEVEL, group_size=GROUP_SIZE)
    return time.perf_counter() - started


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-fused-finalize-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        base_ref = td / "base-ref.cmpct"
        fused_ref = td / "fused-ref.cmpct"
        BASE.build(stage, base_ref, level=LEVEL, group_size=GROUP_SIZE)
        fused_stats = FUSED.build(stage, fused_ref, level=LEVEL, group_size=GROUP_SIZE)
        base_bytes = base_ref.read_bytes()
        fused_bytes = fused_ref.read_bytes()
        if fused_bytes != base_bytes:
            raise RuntimeError("fused ZIP-factor finalize changed exact CMP25Z3 bytes")
        verified = BASE.strong_verify(fused_ref)
        if not verified.get("ok"):
            raise RuntimeError(f"fused ZIP-factor archive failed strong verification: {verified}")

        samples = {"baseline": [], "candidate": []}
        orders = (("baseline", "candidate"), ("candidate", "baseline"))
        for round_index in range(ROUNDS):
            round_dir = td / f"round-{round_index}"
            round_dir.mkdir()
            for name in orders[round_index % 2]:
                archive = round_dir / f"{name}.cmpct"
                elapsed = _timed(BASE.build if name == "baseline" else FUSED.build, stage, archive)
                if archive.read_bytes() != base_bytes:
                    raise RuntimeError(f"{name} timed build drifted from exact reference bytes")
                samples[name].append(elapsed)

        medians = {name: statistics.median(values) for name, values in samples.items()}
        absolute = medians["baseline"] - medians["candidate"]
        relative = absolute / medians["baseline"] if medians["baseline"] else 0.0
        material = absolute >= MIN_ABSOLUTE_SPEEDUP_S and relative >= MIN_RELATIVE_SPEEDUP
        return {
            "schema": "cmpct-v030-zipfactor-fused-finalize-oracle-v1",
            "contract": {
                "rounds": ROUNDS,
                "level": LEVEL,
                "group_size": GROUP_SIZE,
                "exact_archive_bytes_required": True,
                "strong_verification_required": True,
                "min_relative_speedup": MIN_RELATIVE_SPEEDUP,
                "min_absolute_speedup_s": MIN_ABSOLUTE_SPEEDUP_S,
                "selector_change": False,
                "release_credit": False,
            },
            "candidate": {
                "archive_bytes": len(base_bytes),
                "archive_sha256": hashlib.sha256(base_bytes).hexdigest(),
                "fused_group_finalize": bool(fused_stats.get("fused_group_finalize")),
                "max_member_read_amplification": float(fused_stats["max_member_read_amplification"]),
                "max_decode_unit_bytes": int(fused_stats["max_decode_unit_bytes"]),
            },
            "samples_s": samples,
            "medians_s": medians,
            "absolute_speedup_s": absolute,
            "relative_speedup": relative,
            "exact_byte_identity": True,
            "experiment_valid": True,
            "promotion_signal": material,
            "release_credit": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("ZIP-factor fused-finalize experiment invalid")


if __name__ == "__main__":
    main()
